from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import asyncio
import json
from typing import AsyncGenerator

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


@app.post("/api/chat-stream")
async def chat_stream(req: ChatRequest):
    """Server-Sent Events stream of reply tokens.

    Events:
      - event: init, data: { session_id, suggestions, topic, escalate }
      - event: token, data: <partial text>
      - event: done, data: { reply }
    """

    async def event_gen() -> AsyncGenerator[bytes, None]:
        def sse(event: str, data: str) -> bytes:
            return f"event: {event}\ndata: {data}\n\n".encode("utf-8")

        # Ensure session and record user message
        sid = agent._ensure_session(req.session_id)
        agent.sessions[sid].append(("user", req.message))

        # Determine topic + suggestions + escalate
        topic = agent._detect_topic(req.message)
        if topic == "unknown":
            suggestions = [
                "Show plan options",
                "Check data balance",
                "View my bill",
                "Roaming rates",
                "Coverage map",
                "Talk to an agent",
            ]
            escalate = False
        else:
            suggestions = agent.knowledge[topic]["suggestions"]
            escalate = topic == "support" or any(
                w in req.message.lower() for w in ["agent", "human", "person", "escalate"]
            )

        # Send init metadata first
        init_payload = json.dumps(
            {
                "session_id": sid,
                "suggestions": suggestions,
                "topic": topic,
                "escalate": escalate,
            },
            ensure_ascii=False,
        )
        yield sse("init", init_payload)

        full_reply: str = ""

        # Stream via OpenAI when configured; otherwise simulate streaming
        if agent._llm_client is not None:
            try:
                system = (
                    f"You are a concise, friendly mobile network provider support chatbot for {agent.provider}. "
                    "Answer helpfully for telecom topics like plans, upgrades, data/balance, billing, roaming, network/coverage, devices/SIM. "
                    "Avoid hallucinations; if uncertain, ask for details or suggest contacting a human agent."
                )
                messages = [{"role": "system", "content": system}]
                history = agent.sessions.get(sid, [])
                for role, text in history[-6:]:
                    messages.append({"role": role, "content": text})
                messages.append({"role": "user", "content": req.message})

                stream = agent._llm_client.chat.completions.create(
                    model=agent._llm_model,
                    messages=messages,  # type: ignore
                    temperature=0.3,
                    max_tokens=220,
                    stream=True,
                )

                for chunk in stream:  # type: ignore
                    try:
                        delta = chunk.choices[0].delta if chunk.choices else None
                        token = getattr(delta, "content", None) if delta is not None else None
                    except Exception:
                        token = None
                    if token:
                        full_reply += token
                        yield sse("token", token)
                        await asyncio.sleep(0)  # let event loop flush
            except Exception:
                # Fallback to non-LLM canned reply if streaming fails
                reply = (
                    agent.knowledge.get(topic, {}).get("reply")
                    if topic in agent.knowledge
                    else (
                        f"I'm your {agent.provider} virtual assistant. I can help with plans, "
                        "data/balance, billing, roaming, coverage, or devices. Could you share a few details?"
                    )
                ) or "Sorry, I ran into an issue."
                for part in _chunk_text_for_stream(reply):
                    full_reply += part
                    yield sse("token", part)
                    await asyncio.sleep(0)
        else:
            # Rule-based reply; stream in small chunks
            if topic == "unknown":
                reply = (
                    f"I'm your {agent.provider} virtual assistant. I can help with plans, "
                    "data/balance, billing, roaming, coverage, or devices. Could you share a few details?"
                )
            else:
                reply = agent.knowledge[topic]["reply"]
            for part in _chunk_text_for_stream(reply):
                full_reply += part
                yield sse("token", part)
                await asyncio.sleep(0)

        # Save assistant reply to history and send done
        agent.sessions[sid].append(("assistant", full_reply))
        done_payload = json.dumps({"reply": full_reply}, ensure_ascii=False)
        yield sse("done", done_payload)

    def _chunk_text_for_stream(text: str):
        # Simple word-respecting chunker ~40 chars
        buf = []
        count = 0
        for word in text.split(" "):
            if count + len(word) + (1 if buf else 0) > 40:
                yield (" ".join(buf)) + " "
                buf = [word]
                count = len(word)
            else:
                buf.append(word)
                count += len(word) + (1 if count > 0 else 0)
        if buf:
            yield " ".join(buf)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # for proxies like nginx
        },
    )
