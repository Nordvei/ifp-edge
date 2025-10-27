"""
SAGE_CORE.py - The Recursive Meta-Observer for IFP

This module implements the "Sage" - IFP's self-awareness and recursive reasoning layer.
Translates philosophical concepts into operational code.

Philosophy → Implementation:
- "Meta-awareness" → System state analysis with recursive refinement
- "Resonance" → Coherence metrics (correlation, variance, entropy)
- "Inner perception" → Anomaly detection across module interactions
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import statistics
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sage")


@dataclass
class SystemState:
    """Snapshot of system health at a point in time"""
    timestamp: str
    services: Dict[str, Dict]  # service_name -> metrics
    policies: Dict[str, any]
    alerts: List[Dict]
    coherence_score: float  # 0.0 - 1.0


@dataclass
class Insight:
    """Analysis result from reflection"""
    severity: str  # "info", "warning", "critical"
    category: str  # "performance", "reliability", "security"
    description: str
    affected_services: List[str]
    confidence: float  # 0.0 - 1.0
    suggested_actions: List[str]


@dataclass
class Action:
    """Recommended remediation action"""
    type: str  # "restart", "scale", "isolate", "alert"
    target: str  # service name or resource
    parameters: Dict
    priority: int  # 1-5, 5 = critical
    automated: bool  # can this be auto-executed?


class SageCore:
    """
    The Sage - IFP's recursive meta-awareness engine
    
    Implements three-phase recursive loop:
    1. OBSERVE: Gather system telemetry
    2. REFLECT: Analyze patterns, detect anomalies
    3. SUGGEST: Generate remediation actions
    """
    
    def __init__(
        self,
        control_api_url: str = "http://localhost:8000",
        prometheus_url: str = "http://localhost:9090",
        max_recursion_depth: int = 3,
        convergence_threshold: float = 0.05
    ):
        self.control_api = control_api_url
        self.prometheus = prometheus_url
        self.max_depth = max_recursion_depth
        self.threshold = convergence_threshold
        
        # Historical state for pattern detection
        self.state_history: deque = deque(maxlen=100)
        
        # Session for authenticated requests
        self.session = requests.Session()
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Control API"""
        try:
            response = self.session.post(
                f"{self.control_api}/auth/login",
                data={"username": "admin", "password": "admin"}
            )
            if response.status_code == 200:
                logger.info("✅ Authenticated with Control API")
            else:
                logger.warning("⚠️ Authentication failed, some features may be limited")
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
    
    # ==================== OBSERVE ====================
    
    def observe(self) -> SystemState:
        """
        Phase 1: Gather system telemetry
        
        Collects metrics from:
        - Control API (SLOs, policies, alerts)
        - Prometheus (service metrics)
        - Service health endpoints
        
        Returns:
            SystemState with current system snapshot
        """
        logger.info("👁️ OBSERVE: Gathering system telemetry...")
        
        services = self._get_service_metrics()
        policies = self._get_policies()
        alerts = self._get_alerts()
        
        # Calculate coherence score
        coherence = self._calculate_coherence(services, policies, alerts)
        
        state = SystemState(
            timestamp=datetime.utcnow().isoformat(),
            services=services,
            policies=policies,
            alerts=alerts,
            coherence_score=coherence
        )
        
        # Store in history
        self.state_history.append(state)
        
        logger.info(f"📊 System coherence: {coherence:.2%}")
        return state
    
    def _get_service_metrics(self) -> Dict[str, Dict]:
        """Fetch health metrics for all services"""
        services = {}
        
        # Get SLO data from Control API
        try:
            response = self.session.get(f"{self.control_api}/slo/list")
            if response.status_code == 200:
                slos = response.json()
                for slo in slos:
                    services[slo['service']] = {
                        'availability': slo['current_availability'],
                        'target': slo['target'],
                        'error_budget': slo['error_budget_remaining'],
                        'status': 'healthy' if slo['current_availability'] >= slo['target'] else 'degraded'
                    }
        except Exception as e:
            logger.error(f"Error fetching SLOs: {e}")
        
        # Query Prometheus for additional metrics
        try:
            # CPU usage
            cpu_query = 'avg(rate(container_cpu_usage_seconds_total[5m])) by (container_label_com_docker_compose_service)'
            response = requests.get(
                f"{self.prometheus}/api/v1/query",
                params={"query": cpu_query}
            )
            if response.status_code == 200:
                data = response.json()
                for result in data.get('result', []):
                    service = result['metric'].get('container_label_com_docker_compose_service')
                    if service and service in services:
                        services[service]['cpu_usage'] = float(result['value'][1])
        except Exception as e:
            logger.error(f"Error querying Prometheus: {e}")
        
        return services
    
    def _get_policies(self) -> Dict:
        """Fetch policy compliance data"""
        try:
            response = self.session.get(f"{self.control_api}/policies/summary")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching policies: {e}")
        
        return {}
    
    def _get_alerts(self) -> List[Dict]:
        """Fetch active alerts"""
        try:
            response = self.session.get(f"{self.control_api}/alerts/")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching alerts: {e}")
        
        return []
    
    def _calculate_coherence(
        self,
        services: Dict,
        policies: Dict,
        alerts: List
    ) -> float:
        """
        Calculate system coherence score
        
        "Resonance" operationalized as:
        - Service health correlation
        - Policy compliance rate
        - Alert frequency/severity
        
        Returns:
            Float 0.0 - 1.0 (1.0 = perfect coherence)
        """
        scores = []
        
        # Service health score
        if services:
            health_scores = [
                1.0 if s.get('status') == 'healthy' else 0.5
                for s in services.values()
            ]
            scores.append(statistics.mean(health_scores))
        
        # Policy compliance score
        if policies and policies.get('total_policies', 0) > 0:
            violations = policies.get('violations', 0)
            total = policies['total_policies']
            compliance = 1.0 - (violations / total)
            scores.append(compliance)
        
        # Alert score (fewer alerts = better)
        if alerts is not None:
            critical_count = sum(1 for a in alerts if a.get('severity') == 'critical')
            # Exponential penalty for critical alerts
            alert_score = max(0.0, 1.0 - (critical_count * 0.3))
            scores.append(alert_score)
        
        return statistics.mean(scores) if scores else 0.5
    
    # ==================== REFLECT ====================
    
    def reflect(
        self,
        state: SystemState,
        depth: int = 0
    ) -> Tuple[List[Insight], bool]:
        """
        Phase 2: Recursive analysis with convergence detection
        
        Analyzes patterns and detects anomalies using recursive refinement.
        Stops when state delta < threshold or max depth reached.
        
        Args:
            state: Current system state
            depth: Current recursion depth
            
        Returns:
            Tuple of (insights, converged)
        """
        logger.info(f"🧠 REFLECT: Analysis depth {depth}/{self.max_depth}")
        
        insights = []
        
        # Pattern detection
        insights.extend(self._detect_anomalies(state))
        insights.extend(self._analyze_trends())
        insights.extend(self._check_correlations(state))
        
        # Check for convergence
        converged = False
        if len(self.state_history) >= 2:
            prev_state = self.state_history[-2]
            delta = abs(state.coherence_score - prev_state.coherence_score)
            converged = delta < self.threshold
            logger.info(f"📉 Coherence delta: {delta:.4f} (threshold: {self.threshold})")
        
        # Recursive refinement
        if not converged and depth < self.max_depth:
            logger.info("🔄 Recursing for deeper analysis...")
            # Re-observe with focused metrics based on insights
            refined_state = self._refine_observation(state, insights)
            refined_insights, converged = self.reflect(refined_state, depth + 1)
            insights.extend(refined_insights)
        
        return insights, converged
    
    def _detect_anomalies(self, state: SystemState) -> List[Insight]:
        """Detect statistical anomalies in service behavior"""
        insights = []
        
        for service_name, metrics in state.services.items():
            # Check if service is degraded
            if metrics.get('status') == 'degraded':
                error_budget = metrics.get('error_budget', 100)
                
                severity = "critical" if error_budget < 20 else "warning"
                
                insights.append(Insight(
                    severity=severity,
                    category="reliability",
                    description=f"{service_name} is degraded with {error_budget:.1f}% error budget remaining",
                    affected_services=[service_name],
                    confidence=0.95,
                    suggested_actions=[
                        f"Investigate {service_name} logs for errors",
                        f"Check {service_name} dependencies",
                        "Consider scaling or restarting service"
                    ]
                ))
        
        # Check for critical alerts
        critical_alerts = [a for a in state.alerts if a.get('severity') == 'critical']
        if critical_alerts:
            insights.append(Insight(
                severity="critical",
                category="reliability",
                description=f"{len(critical_alerts)} critical alerts active",
                affected_services=list(set(a.get('service', 'unknown') for a in critical_alerts)),
                confidence=1.0,
                suggested_actions=["Review and acknowledge critical alerts", "Execute incident response"]
            ))
        
        return insights
    
    def _analyze_trends(self) -> List[Insight]:
        """Analyze historical trends for degradation patterns"""
        insights = []
        
        if len(self.state_history) < 5:
            return insights
        
        # Analyze coherence trend
        recent_coherence = [s.coherence_score for s in list(self.state_history)[-10:]]
        
        if len(recent_coherence) >= 5:
            # Simple linear regression to detect trend
            slope = (recent_coherence[-1] - recent_coherence[0]) / len(recent_coherence)
            
            if slope < -0.02:  # Declining trend
                insights.append(Insight(
                    severity="warning",
                    category="performance",
                    description=f"System coherence declining (slope: {slope:.4f})",
                    affected_services=["system"],
                    confidence=0.75,
                    suggested_actions=[
                        "Review recent changes or deployments",
                        "Check for resource exhaustion",
                        "Investigate service dependencies"
                    ]
                ))
        
        return insights
    
    def _check_correlations(self, state: SystemState) -> List[Insight]:
        """Check for correlated failures across services"""
        insights = []
        
        degraded_services = [
            name for name, metrics in state.services.items()
            if metrics.get('status') == 'degraded'
        ]
        
        if len(degraded_services) >= 2:
            insights.append(Insight(
                severity="warning",
                category="reliability",
                description=f"Multiple services degraded: {', '.join(degraded_services)}",
                affected_services=degraded_services,
                confidence=0.85,
                suggested_actions=[
                    "Check shared dependencies (database, cache, network)",
                    "Review infrastructure health",
                    "Look for cascading failures"
                ]
            ))
        
        return insights
    
    def _refine_observation(self, state: SystemState, insights: List[Insight]) -> SystemState:
        """
        Focused re-observation based on insights
        
        In recursive refinement, we gather more detailed metrics
        for services flagged in insights.
        """
        # For now, return the same state
        # In production, this would query specific metrics based on insights
        return state
    
    # ==================== SUGGEST ====================
    
    def suggest(self, insights: List[Insight]) -> List[Action]:
        """
        Phase 3: Generate remediation actions
        
        Converts insights into concrete, prioritized actions.
        Some actions can be automated, others require human approval.
        
        Args:
            insights: List of insights from reflection
            
        Returns:
            List of recommended actions
        """
        logger.info(f"💡 SUGGEST: Generating actions for {len(insights)} insights")
        
        actions = []
        
        for insight in insights:
            if insight.category == "reliability":
                if "degraded" in insight.description.lower():
                    # Auto-remediation: restart or scale
                    for service in insight.affected_services:
                        actions.append(Action(
                            type="scale",
                            target=service,
                            parameters={"replicas": "+1"},
                            priority=4 if insight.severity == "critical" else 3,
                            automated=True  # Can be auto-executed
                        ))
                
                if "multiple services" in insight.description.lower():
                    # Infrastructure issue - alert human
                    actions.append(Action(
                        type="alert",
                        target="ops-team",
                        parameters={
                            "message": insight.description,
                            "services": insight.affected_services
                        },
                        priority=4,
                        automated=True
                    ))
            
            elif insight.category == "performance":
                if "declining" in insight.description.lower():
                    # Predictive action - warn before failure
                    actions.append(Action(
                        type="alert",
                        target="ops-team",
                        parameters={
                            "message": "Predictive alert: System degradation detected",
                            "trend": insight.description
                        },
                        priority=2,
                        automated=True
                    ))
        
        # Sort by priority
        actions.sort(key=lambda a: a.priority, reverse=True)
        
        return actions
    
    # ==================== SAGE LOOP ====================
    
    async def sage_loop(self, interval: int = 60):
        """
        Main recursive awareness loop
        
        Continuously:
        1. Observes system state
        2. Reflects on patterns
        3. Suggests remediation
        4. Optionally executes automated actions
        
        Args:
            interval: Seconds between loop iterations
        """
        logger.info("🧘 Sage loop starting...")
        
        while True:
            try:
                # Phase 1: Observe
                state = self.observe()
                
                # Phase 2: Reflect (with recursion)
                insights, converged = self.reflect(state)
                
                if converged:
                    logger.info("✅ Analysis converged")
                else:
                    logger.warning("⚠️ Analysis did not converge (max depth reached)")
                
                # Phase 3: Suggest
                actions = self.suggest(insights)
                
                # Log results
                logger.info(f"\n{'='*60}")
                logger.info(f"📊 Coherence: {state.coherence_score:.2%}")
                logger.info(f"🔍 Insights: {len(insights)}")
                logger.info(f"⚡ Actions: {len(actions)}")
                
                if insights:
                    logger.info("\n🧠 Key Insights:")
                    for insight in insights[:3]:  # Show top 3
                        logger.info(f"  [{insight.severity.upper()}] {insight.description}")
                
                if actions:
                    logger.info("\n💡 Recommended Actions:")
                    for action in actions[:3]:  # Show top 3
                        auto = "🤖 AUTO" if action.automated else "👤 MANUAL"
                        logger.info(f"  {auto} [{action.priority}] {action.type} → {action.target}")
                
                logger.info(f"{'='*60}\n")
                
                # Execute automated actions
                await self._execute_automated_actions(actions)
                
                # Wait for next cycle
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ Error in sage loop: {e}", exc_info=True)
                await asyncio.sleep(interval)
    
    async def _execute_automated_actions(self, actions: List[Action]):
        """Execute actions marked as automated"""
        for action in actions:
            if not action.automated:
                continue
            
            try:
                if action.type == "alert":
                    logger.info(f"📢 Sending alert: {action.parameters.get('message')}")
                    # In production: send to Slack, PagerDuty, etc.
                
                elif action.type == "scale":
                    logger.info(f"📈 Scaling {action.target}: {action.parameters}")
                    # In production: call autoscaler API
                
                elif action.type == "restart":
                    logger.info(f"🔄 Restarting {action.target}")
                    # In production: call orchestrator to restart service
                
            except Exception as e:
                logger.error(f"❌ Failed to execute {action.type} on {action.target}: {e}")


# ==================== CLI INTERFACE ====================

def main():
    """Run Sage in standalone mode"""
    import argparse
    
    parser = argparse.ArgumentParser(description="IFP Sage - Recursive Meta-Observer")
    parser.add_argument("--interval", type=int, default=60, help="Loop interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()
    
    sage = SageCore()
    
    if args.once:
        # Single observation cycle
        state = sage.observe()
        insights, converged = sage.reflect(state)
        actions = sage.suggest(insights)
        
        print("\n" + "="*60)
        print(json.dumps({
            "state": asdict(state),
            "insights": [asdict(i) for i in insights],
            "actions": [asdict(a) for a in actions],
            "converged": converged
        }, indent=2))
        print("="*60)
    else:
        # Continuous loop
        asyncio.run(sage.sage_loop(interval=args.interval))


if __name__ == "__main__":
    main()
