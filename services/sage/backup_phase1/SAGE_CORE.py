from fastapi import FastAPI
from pydantic import BaseModel
import os, time, requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONTROL_API = os.getenv("CONTROL_API", "http://control-api:8000")
INTERVAL_S = int(os.getenv("SAGE_INTERVAL_S", "30"))
O2_MONITORING_ENABLED = os.getenv("O2_MONITORING_ENABLED", "true").lower() == "true"

app = FastAPI(title="IFP Sage (Edge)", version="0.2.0")

class Health(BaseModel):
    status: str
    mode: str
    interval_s: int
    o2_monitoring: bool = False

@app.get("/health", response_model=Health)
def health():
    return Health(
        status="ok",
        mode="edge-only",
        interval_s=INTERVAL_S,
        o2_monitoring=O2_MONITORING_ENABLED
    )

def quick_observe():
    # Minimal telemetry pull to prove the loop without heavy RAM use
    observations = {}

    # Check Control API
    try:
        r = requests.get(f"{CONTROL_API}/health", timeout=3)
        r.raise_for_status()
        observations["control_api"] = "up"
        observations["control_payload"] = r.json()
    except Exception as e:
        observations["control_api"] = "down"
        observations["control_error"] = str(e)

    # Check O2 Wallet if enabled
    if O2_MONITORING_ENABLED:
        try:
            from o2_monitor import observe_o2
            observations["o2"] = observe_o2()
        except Exception as e:
            logger.error(f"O2 monitoring failed: {e}")
            observations["o2"] = {"status": "error", "error": str(e)}

    return observations

def quick_reflect(state):
    # Replace "resonance" with a bounded, numeric coherence score
    # Simple first cut: 1.0 if control-api up, else 0.0
    insights = {
        "control_coherence": 1.0 if state.get("control_api") == "up" else 0.0
    }

    # Add O2 insights if available
    if "o2" in state and O2_MONITORING_ENABLED:
        try:
            from o2_monitor import reflect_o2
            o2_insights = reflect_o2(state["o2"])
            insights.update(o2_insights)

            # Overall coherence is average of control and O2
            insights["coherence"] = (insights["control_coherence"] + o2_insights.get("o2_coherence", 0)) / 2
        except Exception as e:
            logger.error(f"O2 reflection failed: {e}")
            insights["coherence"] = insights["control_coherence"]
    else:
        insights["coherence"] = insights["control_coherence"]

    return insights

def quick_act(insights):
    # No auto-remediation in v0.2. Emit as a log/heartbeat for Control API ingestion
    try:
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
        pass

    # Log O2 issues if any
    if "o2_issues" in insights and insights.get("o2_issues"):
        for issue in insights["o2_issues"]:
            severity = issue.get("severity", "info").upper()
            message = issue.get("message", "Unknown O2 issue")
            logger.warning(f"[O2 {severity}] {message}")

if __name__ == "__main__":
    # Background loop (simple, single-threaded, low RAM)
    import threading, uvicorn
    def loop():
        while True:
            s = quick_observe()
            i = quick_reflect(s)
            quick_act(i)
            time.sleep(INTERVAL_S)
    threading.Thread(target=loop, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8055)
