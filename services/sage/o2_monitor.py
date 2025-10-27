"""
O2 Wallet Monitoring Module for Simple Sage

Lightweight monitoring for O2 wallet service health and balance.
Integrates with the simple Sage loop.
"""
import requests
import logging
import os

logger = logging.getLogger(__name__)

# Configuration
O2_WALLET_API = os.getenv("O2_WALLET_API", "http://ifp-o2-wallet:8085")
LOW_BALANCE_THRESHOLD = float(os.getenv("O2_LOW_BALANCE_THRESHOLD", "10000"))
API_TIMEOUT = 3  # seconds


def check_o2_health():
    """
    Check O2 wallet service health

    Returns:
        dict: O2 health status and observations
    """
    observations = {
        "service": "o2-wallet",
        "status": "unknown",
        "balance": None,
        "issues": []
    }

    try:
        # Check service health
        health_resp = requests.get(
            f"{O2_WALLET_API}/health",
            timeout=API_TIMEOUT
        )
        health_resp.raise_for_status()
        health = health_resp.json()

        observations["status"] = health.get("status", "unknown")
        observations["blockchain_connected"] = health.get("blockchain_connected", False)

        # If service is healthy, check balance
        if observations["status"] == "healthy":
            balance_resp = requests.get(
                f"{O2_WALLET_API}/api/balance",
                timeout=API_TIMEOUT
            )
            balance_resp.raise_for_status()
            balance_data = balance_resp.json()

            balance = balance_data.get("balance", 0)
            observations["balance"] = balance
            observations["wallet_address"] = balance_data.get("wallet_address")

            # Check for low balance
            if balance < LOW_BALANCE_THRESHOLD and balance > 0:
                observations["issues"].append({
                    "type": "low_balance",
                    "severity": "warning",
                    "message": f"O2 balance ({balance:,.0f}) below threshold ({LOW_BALANCE_THRESHOLD:,.0f})",
                    "balance": balance,
                    "threshold": LOW_BALANCE_THRESHOLD
                })

        # Check for blockchain issues
        if not observations.get("blockchain_connected", False):
            observations["issues"].append({
                "type": "blockchain_disconnected",
                "severity": "error",
                "message": "O2 wallet blockchain connection failed"
            })

    except requests.exceptions.Timeout:
        observations["status"] = "timeout"
        observations["issues"].append({
            "type": "service_timeout",
            "severity": "error",
            "message": f"O2 wallet service timeout ({API_TIMEOUT}s)"
        })

    except requests.exceptions.ConnectionError:
        observations["status"] = "unreachable"
        observations["issues"].append({
            "type": "service_unreachable",
            "severity": "error",
            "message": "O2 wallet service unreachable"
        })

    except Exception as e:
        observations["status"] = "error"
        observations["issues"].append({
            "type": "check_failed",
            "severity": "error",
            "message": f"O2 health check failed: {str(e)}"
        })

    return observations


def calculate_o2_coherence(observations):
    """
    Calculate coherence score for O2 wallet (0.0 to 1.0)

    Args:
        observations: O2 observations dict

    Returns:
        float: Coherence score
    """
    if observations["status"] == "healthy":
        score = 1.0

        # Reduce score for each issue
        for issue in observations["issues"]:
            if issue["severity"] == "error":
                score -= 0.3
            elif issue["severity"] == "warning":
                score -= 0.1

        return max(0.0, score)

    elif observations["status"] in ["degraded", "timeout"]:
        return 0.5

    else:
        return 0.0


def get_o2_insights(observations):
    """
    Generate insights from O2 observations

    Args:
        observations: O2 observations dict

    Returns:
        dict: Insights with coherence and recommendations
    """
    coherence = calculate_o2_coherence(observations)

    insights = {
        "o2_coherence": coherence,
        "o2_status": observations["status"],
        "o2_balance": observations.get("balance"),
        "o2_issues_count": len(observations["issues"]),
        "o2_issues": observations["issues"]
    }

    # Add recommendations
    if coherence < 0.7:
        insights["recommendations"] = []

        for issue in observations["issues"]:
            if issue["type"] == "low_balance":
                insights["recommendations"].append("Review O2 token reserves")
            elif issue["type"] == "blockchain_disconnected":
                insights["recommendations"].append("Restart O2 wallet service")
            elif issue["type"] == "service_unreachable":
                insights["recommendations"].append("Check O2 wallet container status")

    return insights


# Simple integration function for Sage loop
def observe_o2():
    """
    Observe O2 wallet state (integrates with Sage loop)

    Returns:
        dict: O2 observations
    """
    return check_o2_health()


def reflect_o2(observations):
    """
    Reflect on O2 observations (integrates with Sage loop)

    Args:
        observations: O2 observations dict

    Returns:
        dict: O2 insights
    """
    return get_o2_insights(observations)


# Test function
if __name__ == "__main__":
    print("Testing O2 Monitor...")
    print("=" * 60)

    obs = observe_o2()
    print(f"\nObservations:")
    print(f"  Status: {obs['status']}")
    print(f"  Balance: {obs.get('balance', 'N/A')}")
    print(f"  Issues: {len(obs['issues'])}")

    if obs['issues']:
        print(f"\nIssues found:")
        for issue in obs['issues']:
            print(f"  - [{issue['severity'].upper()}] {issue['message']}")

    insights = reflect_o2(obs)
    print(f"\nInsights:")
    print(f"  Coherence: {insights['o2_coherence']:.2f}")
    print(f"  Status: {insights['o2_status']}")

    if "recommendations" in insights:
        print(f"\nRecommendations:")
        for rec in insights["recommendations"]:
            print(f"  - {rec}")

    print("\n" + "=" * 60)
