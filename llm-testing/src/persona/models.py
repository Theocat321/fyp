"""Pydantic models for user personas."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ConversationParameters(BaseModel):
    """Parameters controlling conversation behavior."""
    max_patience_turns: int = Field(
        ...,
        description="Maximum number of turns before user becomes frustrated"
    )
    escalation_threshold: int = Field(
        ...,
        description="Number of unsatisfactory responses before requesting escalation"
    )
    tech_literacy: str = Field(
        ...,
        description="User's technical skill level: low, moderate, high"
    )


class BehavioralTraits(BaseModel):
    """Behavioral characteristics of the persona."""
    patience_level: str = Field(..., description="low, moderate, high")
    tone: List[str] = Field(..., description="List of tone descriptors (e.g., frustrated_impatient)")
    response_style: str = Field(..., description="How user structures responses")
    detail_preference: str = Field(..., description="Preference for information detail level")


class Persona(BaseModel):
    """A user persona for simulation."""
    id: str = Field(..., description="Unique identifier for the persona")
    name: str = Field(..., description="Persona's name")
    age: int = Field(..., description="Age in years")
    location: str = Field(..., description="Geographic location")

    demographics: Dict[str, str] = Field(
        ...,
        description="Additional demographic information"
    )

    personality: Dict[str, str] = Field(
        ...,
        description="Personality traits and characteristics"
    )

    behavioral_traits: BehavioralTraits = Field(
        ...,
        description="How the persona behaves in conversations"
    )

    goals: List[str] = Field(
        ...,
        description="What the persona wants to achieve"
    )

    constraints: List[str] = Field(
        default_factory=list,
        description="Limitations or constraints affecting behavior"
    )

    conversation_parameters: ConversationParameters = Field(
        ...,
        description="Technical parameters for conversation simulation"
    )

    seed_utterance: str = Field(
        ...,
        description="Initial message to start the conversation"
    )

    background_context: Optional[str] = Field(
        None,
        description="Additional context about the persona's situation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "persona_001_frustrated_commuter",
                "name": "Alex Chen",
                "age": 34,
                "location": "London",
                "demographics": {
                    "occupation": "Software Developer",
                    "income_level": "middle"
                },
                "personality": {
                    "communication_style": "direct",
                    "emotional_state": "frustrated"
                },
                "behavioral_traits": {
                    "patience_level": "low",
                    "tone": ["frustrated_impatient"],
                    "response_style": "brief and direct",
                    "detail_preference": "minimal"
                },
                "goals": [
                    "Fix network issue immediately",
                    "Get compensation for service disruption"
                ],
                "constraints": [
                    "Limited time during commute",
                    "High stress from repeated issues"
                ],
                "conversation_parameters": {
                    "max_patience_turns": 4,
                    "escalation_threshold": 2,
                    "tech_literacy": "moderate"
                },
                "seed_utterance": "Signal keeps dropping on my train. This is ridiculous. Fix it now."
            }
        }
