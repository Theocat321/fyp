from typing import List, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    participant_group: Optional[str] = None


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
    client_ts: Optional[str] = None  # ISO string
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
