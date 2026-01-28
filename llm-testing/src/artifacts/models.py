"""Pydantic models for experiment artifacts."""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    """A single turn in the conversation."""
    turn_number: int
    speaker: str  # "user" or "assistant"
    message: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class EvaluationScores(BaseModel):
    """Scores from LLM judge evaluation."""
    task_success: float = Field(..., ge=0.0, le=1.0)
    clarity: float = Field(..., ge=0.0, le=1.0)
    empathy: float = Field(..., ge=0.0, le=1.0)
    policy_compliance: float = Field(..., ge=0.0, le=1.0)
    overall_weighted: float = Field(..., ge=0.0, le=1.0)
    rationale: str = Field(..., description="Judge's explanation for scores")


class HeuristicCheckResult(BaseModel):
    """Result from a heuristic check."""
    check_name: str
    passed: bool
    details: Optional[str] = None
    severity: str = Field(
        default="info",
        description="info, warning, critical"
    )


class HeuristicResults(BaseModel):
    """All heuristic check results."""
    checks: List[HeuristicCheckResult]
    all_passed: bool
    critical_failures: List[str] = Field(default_factory=list)


class TerminationInfo(BaseModel):
    """Information about conversation termination."""
    reason: str  # max_turns, escalation, satisfaction, stalemate
    turn_number: int
    details: Optional[str] = None


class ConversationRun(BaseModel):
    """Complete record of a single conversation run."""
    run_id: str
    experiment_id: str
    persona_id: str
    scenario_id: str
    variant: str  # "A" or "B"

    # Conversation data
    transcript: List[ConversationTurn]
    termination: TerminationInfo

    # Evaluation results
    llm_evaluation: EvaluationScores
    heuristic_results: HeuristicResults

    # Metadata
    seed: int
    started_at: datetime
    completed_at: datetime
    total_turns: int
    average_latency_ms: float

    # Configuration snapshot
    config_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Relevant configuration at time of run"
    )


class SummaryStatistics(BaseModel):
    """Aggregated statistics for an experiment."""
    total_conversations: int
    successful_conversations: int  # task_success >= 0.7

    # Average scores
    avg_task_success: float
    avg_clarity: float
    avg_empathy: float
    avg_policy_compliance: float
    avg_overall_score: float

    # Termination breakdown
    termination_reasons: Dict[str, int]

    # Heuristic pass rates
    heuristic_pass_rate: float
    critical_failure_rate: float

    # Performance
    avg_conversation_length: float
    avg_latency_ms: float

    # By persona (optional)
    scores_by_persona: Optional[Dict[str, float]] = None

    # By scenario (optional)
    scores_by_scenario: Optional[Dict[str, float]] = None


class ExperimentRun(BaseModel):
    """Complete experiment run with all conversations."""
    experiment_id: str
    experiment_name: str
    variant: str

    # Results
    conversations: List[ConversationRun]
    summary: SummaryStatistics

    # Metadata
    started_at: datetime
    completed_at: datetime
    total_duration_seconds: float

    # Configuration
    personas_tested: List[str]
    scenarios_tested: List[str]
    seed: int

    # Environment info
    openai_model_simulator: str
    openai_model_judge: str
    vodacare_api_url: str

    class Config:
        json_schema_extra = {
            "example": {
                "experiment_id": "exp_20260128_143022",
                "experiment_name": "variant_a_baseline",
                "variant": "A",
                "conversations": [],
                "summary": {
                    "total_conversations": 25,
                    "successful_conversations": 20,
                    "avg_task_success": 0.82,
                    "avg_clarity": 0.88,
                    "avg_empathy": 0.75,
                    "avg_policy_compliance": 0.95,
                    "avg_overall_score": 0.83,
                    "termination_reasons": {
                        "satisfaction": 18,
                        "max_turns": 5,
                        "escalation": 2
                    },
                    "heuristic_pass_rate": 0.96,
                    "critical_failure_rate": 0.04,
                    "avg_conversation_length": 6.2,
                    "avg_latency_ms": 1250.0
                },
                "started_at": "2026-01-28T14:30:22",
                "completed_at": "2026-01-28T14:45:15",
                "total_duration_seconds": 893.0,
                "personas_tested": ["persona_001", "persona_002"],
                "scenarios_tested": ["scenario_001", "scenario_002"],
                "seed": 42,
                "openai_model_simulator": "gpt-4o-mini",
                "openai_model_judge": "gpt-4o",
                "vodacare_api_url": "http://localhost:8000"
            }
        }
