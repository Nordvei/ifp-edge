"""
IFP Sage - Production-Ready Edge Monitoring with O2 Integration

Combines simple synchronous operation with production features:
- Prometheus metrics collection
- O2 wallet rules engine
- Slack alerting
- Control API monitoring
"""
from fastapi import FastAPI
from pydantic import BaseModel
import os
import time
import requests
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
CONTROL_API = os.getenv("CONTROL_API", "http://control-api:8000")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
DRONE_BRIDGE_URL = os.getenv("DRONE_BRIDGE_URL", "http://drone-bridge:8090")
INTERVAL_S = int(os.getenv("SAGE_INTERVAL_S", "30"))
O2_MONITORING_ENABLED = os.getenv("O2_MONITORING_ENABLED", "true").lower() == "true"

# Predictive Analytics Configuration (Phase 2)
TTE_ALERT_MINUTES = int(os.getenv("O2_TTE_ALERT_MINUTES", "30"))          # Critical TTE threshold
MIN_DRAIN_RATE_TOKENS_PER_H = float(os.getenv("O2_MIN_DRAIN_TPH", "50")) # Ignore tiny drips
CORR_MIN_WALLETS = int(os.getenv("O2_CORR_MIN_WALLETS", "3"))            # Min wallets for correlation
ALERT_COOLDOWN_SEC = int(os.getenv("O2_ALERT_COOLDOWN_SEC", "900"))      # 15min cooldown per wallet

# Alert rate limiting cache
_last_alert = {}  # {(wallet, severity): last_timestamp}

app = FastAPI(title="IFP Sage (Production Edge)", version="1.0.0")


class Health(BaseModel):
    status: str
    mode: str
    interval_s: int
    o2_monitoring: bool = False
    prometheus_enabled: bool = False
    slack_enabled: bool = False


@app.get("/health", response_model=Health)
def health():
    return Health(
        status="ok",
        mode="production-edge",
        interval_s=INTERVAL_S,
        o2_monitoring=O2_MONITORING_ENABLED,
        prometheus_enabled=bool(PROMETHEUS_URL),
        slack_enabled=bool(SLACK_WEBHOOK_URL)
    )


# ============================================================================
# PROMETHEUS INTEGRATION (from reference architecture)
# ============================================================================

def _prom(promql: str, timeout: int = 5) -> List[Dict]:
    """Query Prometheus instant vector API."""
    if not PROMETHEUS_URL:
        return []

    try:
        r = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": promql},
            timeout=timeout,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "success":
            logger.warning(f"PromQL not success: {data}")
            return []
        return data["data"]["result"]
    except Exception as e:
        logger.error(f"Prometheus query error: {e}")
        return []


def _collect_o2_wallets() -> Dict[str, Dict]:
    """Read o2_wallet_balance from Prometheus and map to services dict

    Returns dict with canonical schema:
    - wallet.balance_wei: int (canonical, always in wei)
    - wallet.balance_tokens: float (convenience, for UI)
    - balance: float (legacy, maintained for backwards compatibility)
    - status: str (healthy/degraded)
    """
    services = {}
    results = _prom('o2_wallet_balance')

    for vec in results:
        labels = vec.get("metric", {})
        # Try to get address from label, fall back to default wallet
        address = labels.get("wallet", labels.get("address", "0x638C70f337fc63DB0E108308E3dD60f71eb97342"))

        value_str = vec.get("value", ["0", "0"])[1]
        try:
            bal = float(value_str)
        except Exception:
            bal = 0.0

        # Heuristic: if value is astronomical, assume wei and derive tokens; else assume tokens
        # This handles both wei-based and token-based exporters
        if bal > 1e12:  # looks like wei
            balance_wei = int(bal)
            balance_tokens = bal / 1e18
        else:           # looks like tokens
            balance_tokens = bal
            balance_wei = int(bal * 1e18)

        # Service key includes address for multi-wallet uniqueness
        key = f"o2-wallet:{address.lower()}"

        services[key] = {
            # Canonical fields used by rules
            "wallet.balance_wei": balance_wei,
            "wallet.balance_tokens": balance_tokens,
            "status": "degraded" if balance_wei == 0 else "healthy",

            # Keep legacy fields for backwards compatibility
            "wallet_address": address,
            "balance": balance_tokens,
        }

    return services


def _collect_all_services() -> Dict[str, Dict]:
    """
    Collect all services from Prometheus targets (not just O2 wallet).

    Queries Prometheus /api/v1/targets to discover all scraped services
    and gathers basic health metrics.

    Returns dict with service status and basic metrics.
    """
    services = {}

    try:
        # Query Prometheus targets API
        r = requests.get(f"{PROMETHEUS_URL}/api/v1/targets", timeout=5)
        r.raise_for_status()
        data = r.json()

        if data.get("status") != "success":
            logger.warning(f"Prometheus targets query not successful: {data}")
            return services

        targets = data.get("data", {}).get("activeTargets", [])
        logger.info(f"Found {len(targets)} Prometheus targets")

        for target in targets:
            labels = target.get("labels", {})
            job = labels.get("job", "unknown")
            instance = labels.get("instance", "unknown")
            health = target.get("health", "unknown")
            last_scrape = target.get("lastScrape", "")
            scrape_duration = target.get("scrapeDuration", 0)

            # Create service key
            service_key = f"{job}:{instance}"

            services[service_key] = {
                "job": job,
                "instance": instance,
                "health": health,
                "status": "healthy" if health == "up" else "degraded",
                "last_scrape": last_scrape,
                "scrape_duration_seconds": scrape_duration,
                "labels": labels
            }

            logger.debug(f"Collected service: {service_key} - health={health}")

    except Exception as e:
        logger.error(f"Failed to collect Prometheus targets: {e}")

    return services


def _merge_services(base: Dict[str, Dict], extra: Dict[str, Dict]) -> Dict[str, Dict]:
    """Merge two service dicts without overwriting"""
    merged = dict(base)
    for k, v in extra.items():
        merged[k] = {**merged.get(k, {}), **v}
    return merged


# ============================================================================
# O2 RULES ENGINE (from reference architecture)
# ============================================================================

# Rule definitions (simplified from full O2 rules)
O2_RULES = [
    {
        "id": "o2_low_balance",
        "desc": "O2 wallet balance critically low",
        "predicate": {
            "field": "balance",
            "op": "<",
            "threshold": 10000
        },
        "severity": "warning",
        "action": "alert"
    },
    {
        "id": "o2_zero_balance",
        "desc": "O2 wallet balance is zero",
        "predicate": {
            "field": "balance",
            "op": "==",
            "threshold": 0
        },
        "severity": "critical",
        "action": "alert"
    },
    {
        "id": "o2_service_down",
        "desc": "O2 wallet service unreachable",
        "predicate": {
            "field": "status",
            "op": "==",
            "threshold": "degraded"
        },
        "severity": "error",
        "action": "alert"
    }
]

# Infrastructure monitoring rules (Phase 5.6 - Drone Integration)
INFRASTRUCTURE_RULES = [
    {
        "id": "hvac_temp_critical",
        "desc": "HVAC temperature critically high",
        "predicate": {
            "field": "hvac_temp",
            "op": ">",
            "threshold": 85  # °F
        },
        "severity": "critical",
        "action": "dispatch_drone"
    },
    {
        "id": "hvac_offline",
        "desc": "HVAC system offline",
        "predicate": {
            "field": "hvac_status",
            "op": "==",
            "threshold": "offline"
        },
        "severity": "error",
        "action": "dispatch_drone"
    },
    {
        "id": "power_anomaly",
        "desc": "Power consumption anomaly detected",
        "predicate": {
            "field": "power_watts",
            "op": ">",
            "threshold": 50000  # Watts
        },
        "severity": "warning",
        "action": "dispatch_drone"
    }
]


# ============================================================================
# DRONE DISPATCH ACTION (Phase 5.6)
# ============================================================================

def dispatch_drone(alert_data: Dict) -> Dict:
    """
    Dispatch drone for infrastructure inspection

    Args:
        alert_data: Alert context (service, severity, description)

    Returns:
        Dispatch result with mission_id
    """
    try:
        mission_id = f"ifp-{alert_data['service']}-{int(time.time())}"

        # Define waypoints based on facility location
        # TODO: Get from facility database
        waypoints = [
            {"lat": -35.363261, "lon": 149.165230, "alt": 15},  # Takeoff point
            {"lat": -35.363461, "lon": 149.165430, "alt": 15},  # Infrastructure location
            {"lat": -35.363261, "lon": 149.165230, "alt": 10},  # Return home
        ]

        payload = {
            "mission_id": mission_id,
            "waypoints": waypoints,
            "reason": alert_data['description'],
            "priority": 2 if alert_data['severity'] == 'critical' else 1
        }

        response = requests.post(
            f"{DRONE_BRIDGE_URL}/api/drone/mission",
            json=payload,
            timeout=5
        )

        if response.status_code == 200:
            logger.info(f"✅ Drone dispatched: {mission_id}")
            return {"status": "dispatched", "mission_id": mission_id}
        else:
            logger.error(f"❌ Drone dispatch failed: {response.status_code}")
            return {"status": "failed", "error": response.text}

    except Exception as e:
        logger.error(f"❌ Drone dispatch error: {e}")
        return {"status": "error", "error": str(e)}


# ============================================================================
# O2 RULES ENGINE (from reference architecture)
# ============================================================================

def _eval_o2_rules(services: Dict[str, Dict]) -> List[Dict]:
    """
    Evaluate O2 rules against current services state

    Supports both wei and token thresholds:
    - wallet.balance_wei: int (canonical, in wei)
    - wallet.balance_tokens: float (convenience)
    - balance: float (legacy fallback)

    Returns list of insights with fired rules
    """
    logger.info(f"=== DEBUG: _eval_o2_rules called ===")
    logger.info(f"Total services in state: {len(services)}")
    logger.info(f"Service keys: {list(services.keys())}")

    insights = []

    # Extract O2 services (now includes address in key)
    o2_services = {
        svc: data for svc, data in services.items()
        if svc.startswith("o2-wallet")
    }

    logger.info(f"O2 services extracted: {len(o2_services)}")
    logger.info(f"O2 service keys: {list(o2_services.keys())}")

    if o2_services:
        for svc, data in o2_services.items():
            logger.info(f"O2 service [{svc}]: {data}")

    if not o2_services:
        logger.warning("No O2 services found to evaluate!")
        return insights

    # Normalize balances to wei for consistent thresholding
    balances_wei = {}
    for name, svc in o2_services.items():
        if not isinstance(svc, dict):
            continue

        # Prefer wallet.balance_wei, then wallet.balance_tokens, then legacy 'balance'
        bal = svc.get("wallet.balance_wei")
        if bal is None:
            bal = svc.get("wallet.balance_tokens")
            if bal is not None:
                # Convert tokens → wei for consistent thresholding
                bal = int(float(bal) * 1e18)
        if bal is None:
            legacy = svc.get("balance")
            if legacy is not None:
                # Assume legacy is tokens → wei
                bal = int(float(legacy) * 1e18)

        if bal is not None:
            balances_wei[name] = int(bal)

    logger.info(f"Normalized balances (wei): {balances_wei}")

    for rule in O2_RULES:
        rid = rule.get("id")
        pred = rule.get("predicate", {})
        field = pred.get("field")
        op = pred.get("op")
        threshold_wei = pred.get("threshold_wei")
        threshold_tokens = pred.get("threshold")
        severity = rule.get("severity", "info")

        logger.info(f"Evaluating rule: {rid}")
        logger.info(f"  Field: {field}, Op: {op}, Threshold_wei: {threshold_wei}, Threshold_tokens: {threshold_tokens}")

        fired = []

        # Handle balance-based rules (wei or tokens)
        if field in ["wallet.balance_wei", "balance", "wallet.balance_tokens"]:
            for svc, bal_wei in balances_wei.items():
                # Use wei threshold if specified, otherwise convert token threshold to wei
                if threshold_wei is not None:
                    threshold = threshold_wei
                    compare_value = bal_wei
                    logger.info(f"  Service {svc}: balance_wei={bal_wei}, comparing against wei threshold {threshold}")
                elif threshold_tokens is not None:
                    threshold = int(threshold_tokens * 1e18)
                    compare_value = bal_wei
                    logger.info(f"  Service {svc}: balance_wei={bal_wei}, comparing against token threshold {threshold_tokens} ({threshold} wei)")
                else:
                    logger.warning(f"  Rule {rid} has no threshold specified")
                    continue

                # Evaluate predicate
                condition = False
                if op == "<":
                    condition = compare_value < threshold
                    logger.info(f"    Checking: {compare_value} < {threshold} = {condition}")
                elif op == ">":
                    condition = compare_value > threshold
                    logger.info(f"    Checking: {compare_value} > {threshold} = {condition}")
                elif op == "==":
                    condition = compare_value == threshold
                    logger.info(f"    Checking: {compare_value} == {threshold} = {condition}")

                if condition:
                    fired.append(svc)
                    logger.info(f"    ⚠️  Rule {rid} FIRED for {svc}")

        # Handle status-based rules
        elif field == "status":
            threshold = pred.get("threshold")
            for svc, data in o2_services.items():
                value = data.get("status")
                logger.info(f"  Service {svc}: status={value}")

                if value == threshold:
                    fired.append(svc)
                    logger.info(f"    ⚠️  Rule {rid} FIRED for {svc}")

        if fired:
            logger.info(f"✅ Rule {rid} fired for {len(fired)} service(s): {fired}")
            insights.append({
                "rule_id": rid,
                "description": rule.get("desc"),
                "severity": severity,
                "affected_services": fired[:20],  # Limit to 20
                "confidence": 0.95,
                "action": rule.get("action", "log")
            })

    return insights


def _eval_infrastructure_rules(services: Dict[str, Dict]) -> List[Dict]:
    """
    Evaluate infrastructure monitoring rules and dispatch drones when needed

    Returns list of insights with drone dispatch results
    """
    insights = []

    # Extract infrastructure services (hvac, power, cooling, etc.)
    infra_services = {
        svc: data for svc, data in services.items()
        if svc.startswith(("hvac-", "power-", "cooling-"))
    }

    if not infra_services:
        logger.debug("No infrastructure services found to evaluate")
        return insights

    logger.info(f"=== Evaluating infrastructure rules for {len(infra_services)} services ===")

    # Evaluate rules
    for name, svc in infra_services.items():
        for rule in INFRASTRUCTURE_RULES:
            field = rule["predicate"]["field"]
            op = rule["predicate"]["op"]
            threshold = rule["predicate"]["threshold"]

            value = svc.get(field)
            if value is None:
                continue

            # Evaluate predicate
            triggered = False
            if op == ">" and value > threshold:
                triggered = True
            elif op == "<" and value < threshold:
                triggered = True
            elif op == "==" and value == threshold:
                triggered = True
            elif op == "!=" and value != threshold:
                triggered = True

            if triggered:
                insight = {
                    "service": name,
                    "rule_id": rule["id"],
                    "description": rule["desc"],
                    "severity": rule["severity"],
                    "action": rule["action"],
                    "value": value,
                    "threshold": threshold,
                    "affected_services": [name],
                    "confidence": 0.95
                }

                logger.warning(f"🚨 Infrastructure Alert: {rule['id']} - {rule['desc']} (value={value}, threshold={threshold})")

                # Execute action
                if rule["action"] == "dispatch_drone":
                    logger.info(f"🚁 Dispatching drone for {name}...")
                    dispatch_result = dispatch_drone(insight)
                    insight["dispatch_result"] = dispatch_result

                    if dispatch_result.get("status") == "dispatched":
                        logger.info(f"✅ Drone mission {dispatch_result.get('mission_id')} accepted")
                    else:
                        logger.error(f"❌ Drone dispatch failed: {dispatch_result}")

                insights.append(insight)

    return insights


# ============================================================================
# PREDICTIVE ANALYTICS (Phase 2)
# ============================================================================

def _compute_drain_metrics() -> tuple[Dict[str, float], Dict[str, float], Dict[str, Optional[float]]]:
    """
    Compute drain rate and time-to-empty for all O2 wallets.

    Returns:
        balances: {address_lower: balance_tokens_now (float)}
        drains: {address_lower: drain_tokens_per_hour (float)}  # positive = draining
        ttes: {address_lower: tte_minutes (float or None)}     # None if not draining
    """
    # Query Prometheus recording rules
    bal_vec = _prom('o2_balance_tokens_now')
    rate_vec = _prom('o2_drain_rate_tokens_per_hour')

    balances = {}
    drains = {}

    # Parse balance metrics
    for v in bal_vec:
        metric = v.get("metric", {})
        # Try to get wallet address from labels, fallback to service name or default
        addr = metric.get("wallet", metric.get("address", "")).lower()
        if not addr:
            # Single-wallet mode: use service name or default key
            addr = metric.get("service", "o2-wallet")
        try:
            balances[addr] = float(v.get("value", ["0", "0"])[1])
        except Exception:
            pass

    # Parse drain rate metrics
    for v in rate_vec:
        metric = v.get("metric", {})
        # Try to get wallet address from labels, fallback to service name or default
        addr = metric.get("wallet", metric.get("address", "")).lower()
        if not addr:
            # Single-wallet mode: use service name or default key
            addr = metric.get("service", "o2-wallet")
        try:
            rate = float(v.get("value", ["0", "0"])[1])
            # Positive value means draining (balance decreasing)
            drains[addr] = max(0.0, -rate)
        except Exception:
            pass

    # Compute TTE in minutes
    ttes = {}
    eps = 1e-9
    for addr, bal in balances.items():
        drain = drains.get(addr, 0.0)
        if drain >= MIN_DRAIN_RATE_TOKENS_PER_H:
            # TTE = (balance / drain_rate_per_hour) * 60 minutes
            ttes[addr] = (bal / max(drain, eps)) * 60.0
        else:
            ttes[addr] = None  # Not draining or drain too slow

    return balances, drains, ttes


def _predictive_liquidity_insights() -> List[Dict]:
    """
    Generate predictive insights based on drain rate and TTE.

    Generates:
    1. Per-wallet TTE alerts when time-to-empty < threshold
    2. Correlation alerts when multiple wallets drain simultaneously

    Returns list of insights (compatible with existing insights structure)
    """
    insights = []
    balances, drains, ttes = _compute_drain_metrics()
    now = time.time()

    logger.info(f"=== Predictive Analytics ===")
    logger.info(f"Wallets tracked: {len(balances)}")
    logger.info(f"Wallets draining: {sum(1 for t in ttes.values() if t is not None)}")

    # Per-wallet TTE insights
    for addr, tte in ttes.items():
        if tte is None:
            continue

        if tte < TTE_ALERT_MINUTES:
            svc = f"o2-wallet:{addr}"
            bal = balances.get(addr, 0.0)
            drain = drains.get(addr, 0.0)

            # Rate-limit alerts per (wallet, severity)
            key = (addr, "critical")
            if now - _last_alert.get(key, 0) < ALERT_COOLDOWN_SEC:
                logger.debug(f"Alert cooldown active for {addr[:10]}...")
                continue

            _last_alert[key] = now

            desc = f"TTE {tte:.0f}m | Balance {bal:,.0f} O2 | Drain {drain:,.0f} O2/h"
            logger.warning(f"🚨 Predictive Alert: {svc} - {desc}")

            insights.append({
                "rule_id": "o2_predictive_tte",
                "description": f"Wallet will empty in {tte:.0f} minutes",
                "severity": "critical",
                "affected_services": [svc],
                "confidence": 0.9,
                "action": "alert",
                "details": {
                    "tte_minutes": round(tte, 1),
                    "current_balance": round(bal, 2),
                    "drain_rate_per_hour": round(drain, 2)
                }
            })

    # Correlation detection: N or more wallets draining simultaneously
    draining_wallets = [a for a, rate in drains.items() if rate >= MIN_DRAIN_RATE_TOKENS_PER_H]

    if len(draining_wallets) >= CORR_MIN_WALLETS:
        svcs = [f"o2-wallet:{a}" for a in draining_wallets][:20]
        total_drain = sum(drains.get(a, 0) for a in draining_wallets)
        desc = f"Correlated drain: {len(draining_wallets)} wallets draining {total_drain:,.0f} O2/h total"

        # Rate-limit correlation alert
        key = ("_correlated_", "warning")
        if now - _last_alert.get(key, 0) >= ALERT_COOLDOWN_SEC:
            _last_alert[key] = now
            logger.warning(f"⚠️  Pattern detected: {desc}")

            insights.append({
                "rule_id": "o2_correlated_drain",
                "description": desc,
                "severity": "warning",
                "affected_services": svcs,
                "confidence": 0.8,
                "action": "alert",
                "details": {
                    "wallet_count": len(draining_wallets),
                    "total_drain_rate": round(total_drain, 2),
                    "min_drain_threshold": MIN_DRAIN_RATE_TOKENS_PER_H
                }
            })

    return insights


# ============================================================================
# SLACK INTEGRATION (from reference architecture)
# ============================================================================

def _slack_post(text: str, timeout: int = 4) -> bool:
    """Post alert to Slack webhook"""
    if not SLACK_WEBHOOK_URL:
        logger.debug("SLACK_WEBHOOK_URL not set; skipping Slack post.")
        return False

    try:
        r = requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": text},
            timeout=timeout,
        )
        if r.status_code >= 400:
            logger.error(f"Slack webhook error {r.status_code}: {r.text}")
            return False
        logger.info("✅ Slack alert sent")
        return True
    except Exception as e:
        logger.error(f"Slack post failed: {e}")
        return False


# ============================================================================
# OBSERVE / REFLECT / ACT LOOP
# ============================================================================

def observe():
    """
    👁️  OBSERVE: Gather system telemetry

    Combines:
    - Control API health
    - O2 wallet metrics from Prometheus
    - O2 wallet service status
    """
    observations = {
        "services": {},
        "timestamp": time.time()
    }

    # Check Control API
    try:
        r = requests.get(f"{CONTROL_API}/health", timeout=3)
        r.raise_for_status()
        observations["control_api"] = "up"
        observations["control_payload"] = r.json()
    except Exception as e:
        observations["control_api"] = "down"
        observations["control_error"] = str(e)
        logger.error(f"Control API down: {e}")

    # Collect all services from Prometheus targets
    try:
        logger.info("=== DEBUG: Collecting all services from Prometheus ===")
        all_services = _collect_all_services()
        logger.info(f"All services from Prometheus: {len(all_services)}")
        logger.info(f"Service keys: {list(all_services.keys())}")

        observations["services"] = _merge_services(observations["services"], all_services)
        logger.info(f"Total services after merge: {len(observations['services'])}")

    except Exception as e:
        logger.error(f"Service collection failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

    # Collect O2 wallet metrics from Prometheus (for detailed O2 analysis)
    if O2_MONITORING_ENABLED:
        try:
            logger.info("=== DEBUG: Collecting O2 wallets from Prometheus ===")
            o2_services = _collect_o2_wallets()
            logger.info(f"O2 services from Prometheus: {len(o2_services)}")
            logger.info(f"O2 service keys: {list(o2_services.keys())}")

            for svc, data in o2_services.items():
                logger.info(f"  {svc}: {data}")

            logger.info("=== DEBUG: Merging O2 services ===")
            observations["services"] = _merge_services(observations["services"], o2_services)

            o2_count = sum(1 for k in observations["services"].keys() if k.startswith('o2-wallet'))
            logger.info(f"O2 wallets in merged services: {o2_count}")

            if o2_count > 0:
                o2_keys = [k for k in observations["services"].keys() if k.startswith('o2-wallet')]
                logger.info(f"O2 wallet keys after merge: {o2_keys}")
                for key in o2_keys[:1]:  # Show first one
                    logger.info(f"Sample O2 service [{key}]: {observations['services'][key]}")

        except Exception as e:
            logger.error(f"O2 Prometheus collection failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    # Fallback: Direct O2 API check if Prometheus has no data
    if not observations["services"] and O2_MONITORING_ENABLED:
        try:
            from o2_monitor import observe_o2
            o2_obs = observe_o2()

            # Convert to services format
            observations["services"]["o2-wallet"] = {
                "status": o2_obs.get("status", "unknown"),
                "balance": o2_obs.get("balance", 0),
                "issues": o2_obs.get("issues", [])
            }
            logger.debug("Using direct O2 API (Prometheus fallback)")
        except Exception as e:
            logger.error(f"O2 direct monitoring failed: {e}")

    return observations


def reflect(state: Dict) -> Dict:
    """
    🧠 REFLECT: Analyze system state and generate insights

    Calculates:
    - Coherence score
    - O2 rule evaluations
    - Actionable insights
    """
    insights = {
        "control_coherence": 1.0 if state.get("control_api") == "up" else 0.0,
        "o2_insights": [],
        "recommendations": []
    }

    # Evaluate O2 rules
    if O2_MONITORING_ENABLED and state.get("services"):
        try:
            o2_insights = _eval_o2_rules(state["services"])
            insights["o2_insights"] = o2_insights

            # Add to recommendations
            for insight in o2_insights:
                insights["recommendations"].append({
                    "rule": insight["rule_id"],
                    "action": insight["action"],
                    "severity": insight["severity"],
                    "description": insight["description"]
                })

            logger.debug(f"O2 rules fired: {len(o2_insights)}")
        except Exception as e:
            logger.error(f"O2 rule evaluation failed: {e}")

    # Predictive Analytics (Phase 2)
    if O2_MONITORING_ENABLED:
        try:
            predictive_insights = _predictive_liquidity_insights()
            if predictive_insights:
                # Add predictive insights to o2_insights
                insights["o2_insights"].extend(predictive_insights)

                # Add to recommendations
                for insight in predictive_insights:
                    insights["recommendations"].append({
                        "rule": insight["rule_id"],
                        "action": insight["action"],
                        "severity": insight["severity"],
                        "description": insight["description"]
                    })

                logger.info(f"Predictive insights generated: {len(predictive_insights)}")
        except Exception as e:
            logger.error(f"Predictive analytics failed: {e}")

    # Infrastructure Monitoring (Phase 5.6 - Drone Integration)
    if state.get("services"):
        try:
            infrastructure_insights = _eval_infrastructure_rules(state["services"])
            if infrastructure_insights:
                # Add infrastructure insights to o2_insights (for unified alerting)
                insights["o2_insights"].extend(infrastructure_insights)

                # Add to recommendations
                for insight in infrastructure_insights:
                    insights["recommendations"].append({
                        "rule": insight["rule_id"],
                        "action": insight["action"],
                        "severity": insight["severity"],
                        "description": insight["description"]
                    })

                logger.info(f"Infrastructure insights generated: {len(infrastructure_insights)}")
        except Exception as e:
            logger.error(f"Infrastructure rule evaluation failed: {e}")

    # Calculate overall coherence
    if insights["o2_insights"]:
        # Reduce coherence for each fired rule
        penalty = len(insights["o2_insights"]) * 0.1
        insights["coherence"] = max(0.0, insights["control_coherence"] - penalty)
    else:
        insights["coherence"] = insights["control_coherence"]

    return insights


def act(insights: Dict):
    """
    ⚡ ACT: Execute automated actions based on insights

    Actions:
    - Log recommendations
    - Send Slack alerts
    - Report to Control API
    """
    try:
        # Report heartbeat to Control API
        requests.post(
            f"{CONTROL_API}/alerts/ingest",
            json={
                "type": "sage_heartbeat",
                "insights": insights,
                "timestamp": time.time()
            },
            timeout=2
        )
    except Exception:
        pass  # Non-critical

    # Process O2 insights
    for insight in insights.get("o2_insights", []):
        severity = insight["severity"].upper()
        description = insight["description"]
        services = ", ".join(insight["affected_services"])

        # Log the insight
        log_msg = f"[{severity}] {description} - Affected: {services}"

        if severity == "CRITICAL":
            logger.critical(log_msg)
        elif severity == "ERROR":
            logger.error(log_msg)
        elif severity == "WARNING":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        # Send Slack alert for warnings and above
        if insight["action"] == "alert" and severity in ["WARNING", "ERROR", "CRITICAL"]:
            slack_msg = f"🚨 *IFP Sage Alert*\n\n" \
                       f"*Severity:* {severity}\n" \
                       f"*Rule:* {insight['rule_id']}\n" \
                       f"*Description:* {description}\n" \
                       f"*Affected Services:* {services}\n" \
                       f"*Confidence:* {insight['confidence']*100:.0f}%"

            _slack_post(slack_msg)


# ============================================================================
# MAIN LOOP
# ============================================================================

if __name__ == "__main__":
    import threading
    import uvicorn

    logger.info("🚀 Starting IFP Sage (Production Edge)")
    logger.info(f"   Control API: {CONTROL_API}")
    logger.info(f"   Prometheus: {PROMETHEUS_URL}")
    logger.info(f"   O2 Monitoring: {O2_MONITORING_ENABLED}")
    logger.info(f"   Slack Alerts: {'Enabled' if SLACK_WEBHOOK_URL else 'Disabled'}")
    logger.info(f"   Interval: {INTERVAL_S}s")

    def loop():
        """Background observe/reflect/act loop"""
        loop_count = 0
        while True:
            try:
                loop_count += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"👁️  OBSERVE (Loop #{loop_count}): Gathering system telemetry...")

                state = observe()

                logger.info(f"   Control API: {state.get('control_api')}")
                logger.info(f"   Services: {len(state.get('services', {}))}")

                logger.info(f"🧠 REFLECT: Analyzing system state...")
                insights = reflect(state)

                logger.info(f"   Coherence: {insights.get('coherence', 0):.2f}")
                logger.info(f"   O2 Insights: {len(insights.get('o2_insights', []))}")

                if insights.get("o2_insights"):
                    logger.info(f"⚡ ACT: Executing automated actions...")
                    act(insights)
                else:
                    logger.info(f"✅ No actions needed - system healthy")

                time.sleep(INTERVAL_S)

            except Exception as e:
                logger.exception(f"Error in Sage loop: {e}")
                time.sleep(5)

    # Start background loop
    threading.Thread(target=loop, daemon=True).start()

    # Start FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8055)
