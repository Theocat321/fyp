import asyncio
import json
from typing import AsyncGenerator

from fastapi import FastAPI
import logging
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from server.app.agent import SupportAgent

app = FastAPI(title="VodaCare Support API (Vercel) - chat-stream")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = SupportAgent()


@app.post("/")
async def chat_stream(req: dict):
    """SSE stream compatible with the web client.
    Mirrors server/app/main.py:chat_stream but mounted at function root.
    """

    async def event_gen() -> AsyncGenerator[bytes, None]:
        def sse(event: str, data: str) -> bytes:
            return f"event: {event}\ndata: {data}\n\n".encode("utf-8")

        # Ensure session and record user message
        sid = agent._ensure_session(req.get("session_id"))
        user_message = str(req.get("message", ""))
        agent.sessions[sid].append(("user", user_message))

        # Determine topic + escalate; suggestions removed
        topic = agent._detect_topic(user_message)
        suggestions: list[str] = []
        escalate = topic == "support" or any(
            w in user_message.lower() for w in ["agent", "human", "person", "escalate"]
        )

        init_payload = json.dumps(
            {
                "session_id": sid,
                "suggestions": suggestions,
                "topic": topic,
                "escalate": escalate,
                "engine": "openai" if agent._llm_client is not None else "error",
            },
            ensure_ascii=False,
        )
        yield sse("init", init_payload)

        full_reply: str = ""

        # Stream via OpenAI when configured; otherwise return error text
        if agent._llm_client is not None:
            try:
                if agent.mode == "open":
                    system = (
                        f"You are a helpful support agent for {agent.provider}. Keep replies concise. "
                        "You can chat broadly, and for telecom topics (plans, upgrades, data/balance, billing, roaming, network/coverage, devices/SIM) give clear, practical guidance. "
                        "Ask brief follow‑ups when needed. Don't guess."
                    )
                else:
                    system = (
                        f"You are a helpful mobile network support agent for {agent.provider}. Keep replies concise. "
                        "Focus on telecom topics like plans, upgrades, data/balance, billing, roaming, network/coverage and devices/SIM. "
                        "Ask brief follow‑ups when needed. Don't guess."
                    )
                messages = [{"role": "system", "content": system}]
                history = agent.sessions.get(sid, [])
                for role, text in history[-6:]:
                    messages.append({"role": role, "content": text})
                messages.append({"role": "user", "content": user_message})

                stream = agent._llm_client.chat.completions.create(
                    model=agent._llm_model,
                    messages=messages,  # type: ignore
                    temperature=0.5 if agent.mode == "open" else 0.3,
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
                        await asyncio.sleep(0)
            except Exception:
                logger.exception("OpenAI streaming failed (function)")
                reply = "There’s a problem — the chat service isn’t working right now. Please try again later."
                for part in _chunk_text_for_stream(reply):
                    full_reply += part
                    yield sse("token", part)
                    await asyncio.sleep(0)
        else:
            # No LLM configured: send error text
            logger.warning("LLM client not configured (function); sending error text")
            reply = "There’s a problem — the chat service isn’t working right now. Please try again later."
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
            "X-Accel-Buffering": "no",
        },
    )

