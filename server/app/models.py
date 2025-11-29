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
    rating_overall: Optional[int] = None
    rating_helpfulness: Optional[int] = None
    rating_friendliness: Optional[int] = None
    resolved: Optional[bool] = None
    time_to_resolution: Optional[str] = None
    issues: Optional[list[str]] = []
    comments_positive: Optional[str] = None
    comments_negative: Optional[str] = None
    comments_other: Optional[str] = None
    would_use_again: Optional[str] = None
    recommend_nps: Optional[int] = None
    contact_ok: Optional[bool] = None
    contact_email: Optional[str] = None
    user_agent: Optional[str] = None
    page_url: Optional[str] = None
