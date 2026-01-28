"""Pydantic models for test scenarios."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class HappyPathStep(BaseModel):
    """A step in the ideal conversation flow."""
    step_number: int = Field(..., description="Order in the sequence")
    description: str = Field(..., description="What happens in this step")
    expected_info: List[str] = Field(
        ...,
        description="Information that should be provided"
    )


class EdgeCase(BaseModel):
    """Potential complication or edge case."""
    name: str = Field(..., description="Name of the edge case")
    trigger: str = Field(..., description="What causes this edge case")
    expected_handling: str = Field(
        ...,
        description="How the system should respond"
    )


class SuccessCriteria(BaseModel):
    """Criteria for evaluating scenario success."""
    must_provide: List[str] = Field(
        ...,
        description="Information that must be given to the user"
    )
    must_avoid: List[str] = Field(
        default_factory=list,
        description="Actions or information to avoid"
    )
    escalation_conditions: Optional[List[str]] = Field(
        None,
        description="Situations requiring escalation to human agent"
    )


class Scenario(BaseModel):
    """A test scenario for evaluation."""
    id: str = Field(..., description="Unique identifier for the scenario")
    name: str = Field(..., description="Human-readable scenario name")
    topic: str = Field(
        ...,
        description="Main topic (device, roaming, billing, plans, network)"
    )

    context: str = Field(
        ...,
        description="Background context for the scenario"
    )

    happy_path_steps: List[HappyPathStep] = Field(
        ...,
        description="Ideal conversation flow"
    )

    edge_cases: List[EdgeCase] = Field(
        default_factory=list,
        description="Potential complications"
    )

    success_criteria: SuccessCriteria = Field(
        ...,
        description="What constitutes a successful conversation"
    )

    typical_questions: Optional[List[str]] = Field(
        None,
        description="Common questions users ask in this scenario"
    )

    knowledge_requirements: Optional[List[str]] = Field(
        None,
        description="Information the assistant needs to handle this scenario"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "scenario_001_esim_setup",
                "name": "eSIM Setup",
                "topic": "device",
                "context": "User wants to set up eSIM on their new phone",
                "happy_path_steps": [
                    {
                        "step_number": 1,
                        "description": "Verify device compatibility",
                        "expected_info": ["eSIM support check", "device model"]
                    }
                ],
                "edge_cases": [
                    {
                        "name": "incompatible_device",
                        "trigger": "User has older phone without eSIM support",
                        "expected_handling": "Explain physical SIM is required"
                    }
                ],
                "success_criteria": {
                    "must_provide": [
                        "Compatibility check",
                        "Setup instructions",
                        "Activation steps"
                    ],
                    "must_avoid": [
                        "Guaranteeing success without verification"
                    ]
                }
            }
        }
