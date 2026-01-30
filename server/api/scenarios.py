from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Scenario definitions matching LLM testing framework
SCENARIOS = [
    {
        "id": "scenario_001_esim_setup",
        "name": "eSIM Setup",
        "topic": "device",
        "description": "Get help setting up an eSIM on your device",
        "context": "You want to activate an eSIM but need guidance on compatibility and setup steps."
    },
    {
        "id": "scenario_002_roaming_activation",
        "name": "EU Roaming Activation",
        "topic": "roaming",
        "description": "Learn how to activate roaming for EU travel",
        "context": "You're traveling to the EU and need to understand roaming charges and activation."
    },
    {
        "id": "scenario_003_billing_dispute",
        "name": "Billing Dispute",
        "topic": "billing",
        "description": "Resolve an issue with your bill",
        "context": "You've noticed unexpected charges on your bill and want them explained or corrected."
    },
    {
        "id": "scenario_004_plan_upgrade",
        "name": "Plan Upgrade",
        "topic": "plans",
        "description": "Find the best plan for your needs",
        "context": "Your current plan isn't meeting your needs and you want to explore upgrade options."
    },
    {
        "id": "scenario_005_network_issue",
        "name": "Network Issue",
        "topic": "network",
        "description": "Fix connectivity or signal problems",
        "context": "You're experiencing poor signal or connection issues and need troubleshooting help."
    }
]

@router.get("/scenarios")
async def get_scenarios():
    """
    Return list of available test scenarios.

    GET /api/scenarios

    Returns:
        {
            "scenarios": [
                {
                    "id": "scenario_001_esim_setup",
                    "name": "eSIM Setup",
                    "topic": "device",
                    "description": "...",
                    "context": "..."
                },
                ...
            ]
        }
    """
    try:
        return JSONResponse(content={"scenarios": SCENARIOS}, status_code=200)
    except Exception as e:
        logger.exception("Failed to fetch scenarios")
        return JSONResponse(
            content={"error": "Failed to fetch scenarios"},
            status_code=500
        )
