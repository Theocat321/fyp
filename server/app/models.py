from typing import List, Optional, Union
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    participant_group: Optional[str] = None
    participant_id: Optional[str] = None
    page_url: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    suggestions: List[str]
    topic: str
    escalate: bool = False
    session_id: str


class InteractionEvent(BaseModel):
    session_id: str
    participant_id: Optional[str] = None
    participant_group: Optional[str] = None  # 'A' | 'B'
    event: str
    component: Optional[str] = None
    label: Optional[str] = None
    value: Optional[str] = None
    duration_ms: Optional[int] = None
    client_ts: Optional[Union[str, int]] = None  # ISO string or epoch ms
    page_url: Optional[str] = None
    user_agent: Optional[str] = None
    meta: Optional[dict] = None


class ParticipantInsert(BaseModel):
    participant_id: str
    name: Optional[str] = None
    group: Optional[str] = None  # 'A' | 'B'
    session_id: Optional[str] = None
    scenario_id: Optional[str] = None  # NEW: Track which scenario human is testing


class MessageInsert(BaseModel):
    session_id: str
    role: str  # 'user' | 'assistant'
    content: str
    participant_id: Optional[str] = None
    participant_name: Optional[str] = None
    participant_group: Optional[str] = None


class FeedbackInsert(BaseModel):
    session_id: Optional[str] = None
    participant_id: Optional[str] = None
    participant_group: Optional[str] = None
    scenario_id: Optional[str] = None
    # Core ratings matching LLM evaluation rubric
    rating_overall: Optional[int] = None
    rating_task_success: Optional[int] = None  # 50% weight in rubric
    rating_clarity: Optional[int] = None  # 20% weight in rubric
    rating_empathy: Optional[int] = None  # 20% weight in rubric
    rating_accuracy: Optional[int] = None  # 10% weight (policy compliance)
    resolved: Optional[bool] = None  # Yes/No/Partial resolution status
    comments_other: Optional[str] = None  # Optional feedback text
    user_agent: Optional[str] = None
    page_url: Optional[str] = None
