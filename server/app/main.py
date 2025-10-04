from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_allowed_origins, get_provider_name
from .models import ChatRequest, ChatResponse
from .agent import SupportAgent


app = FastAPI(title="VodaCare Support API", version="0.1.0")

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


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = agent.chat(req.message, req.session_id)
    return JSONResponse(result)

