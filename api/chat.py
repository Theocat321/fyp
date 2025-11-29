from fastapi import FastAPI
import logging
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from server.app.agent import SupportAgent
from server.app.models import ChatRequest
from server.app.config import get_allowed_origins, get_provider_name

# FastAPI app for Vercel Python Serverless Function
app = FastAPI(title="VodaCare Support API (Vercel) - chat")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = SupportAgent()


@app.get("/api/health")
def health():
    return {"status": "ok", "provider": get_provider_name()}


@app.post("/")
def chat(req: ChatRequest):
    """Mirror of server/app/main.py /api/chat but mounted at the function root.
    The Vercel route rewrites /api/chat -> /api/chat.py
    """
    # If no LLM, return error style payload instead of rule-based
    if agent._llm_client is None:
        logger.warning("LLM client not configured (function); returning error payload")
        sid = agent._ensure_session(req.session_id)
        agent.sessions[sid].append(("user", req.message))
        topic = agent._detect_topic(req.message)
        reply = "There’s a problem — the chat service isn’t working right now. Please try again later."
        agent.sessions[sid].append(("assistant", reply))
        return JSONResponse(
            {
                "reply": reply,
                "suggestions": [],
                "topic": topic,
                "escalate": topic == "support" or any(
                    w in req.message.lower() for w in ["agent", "human", "person", "escalate"]
                ),
                "session_id": sid,
                "engine": "error",
            }
        )
    try:
        result = agent.chat(req.message, req.session_id)
    except Exception:
        logger.exception("LLM chat failed (function)")
        sid = agent._ensure_session(req.session_id)
        topic = agent._detect_topic(req.message)
        return JSONResponse(
            {
                "reply": "There’s a problem — the chat service isn’t working right now. Please try again later.",
                "suggestions": [],
                "topic": topic,
                "escalate": topic == "support" or any(
                    w in req.message.lower() for w in ["agent", "human", "person", "escalate"]
                ),
                "session_id": sid,
                "engine": "error",
            }
        )
    return JSONResponse(result)
