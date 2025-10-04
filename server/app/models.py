from typing import List, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    suggestions: List[str]
    topic: str
    escalate: bool = False
    session_id: str

