from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    turn_number: int
    speaker: str  # "user" or "assistant"
    message: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class EvaluationScores(BaseModel):
    task_success: float = Field(..., ge=0.0, le=1.0)
    clarity: float = Field(..., ge=0.0, le=1.0)
    empathy: float = Field(..., ge=0.0, le=1.0)
    overall_weighted: float = Field(..., ge=0.0, le=1.0)
    rationale: str


class HeuristicCheckResult(BaseModel):
    check_name: str
    passed: bool
    details: Optional[str] = None
    severity: str = Field(default="info", description="info, warning, or critical")


class HeuristicResults(BaseModel):
    checks: List[HeuristicCheckResult]
    all_passed: bool
    critical_failures: List[str] = Field(default_factory=list)


class TerminationInfo(BaseModel):
    reason: str  # max_turns, escalation, satisfaction, stalemate
    turn_number: int
    details: Optional[str] = None


class ConversationRun(BaseModel):
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

    config_snapshot: Dict[str, Any] = Field(default_factory=dict)


class SummaryStatistics(BaseModel):
    total_conversations: int
    successful_conversations: int  # task_success >= 0.7

    # Average scores
    avg_task_success: float
    avg_clarity: float
    avg_empathy: float
    avg_overall_score: float

    # Termination breakdown
    termination_reasons: Dict[str, int]

    # Heuristic pass rates
    heuristic_pass_rate: float
    critical_failure_rate: float

    # Performance
    avg_conversation_length: float
    avg_latency_ms: float

    scores_by_persona: Optional[Dict[str, float]] = None
    scores_by_scenario: Optional[Dict[str, float]] = None


class ExperimentRun(BaseModel):
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
