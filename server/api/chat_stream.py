import asyncio
import json
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from datetime import datetime, timezone
import logging
from fastapi.responses import StreamingResponse
import time
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
@app.post("/api/chat-stream")
async def chat_stream(req: dict, request: Request):
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
        # Server-side telemetry: reply_init
        try:
            from server.app.storage import SupabaseStore
            ua = request.headers.get("user-agent") if request else None
            SupabaseStore().insert_rows(
                "interaction_events",
                [
                    {
                        "session_id": sid,
                        "participant_group": req.get("participant_group"),
                        "participant_id": req.get("participant_id"),
                        "event": "reply_init",
                        "component": "chat_stream",
                        "label": "stream_init",
                        "value": None,
                        "duration_ms": None,
                        "client_ts": datetime.now(timezone.utc).isoformat(),
                        "page_url": req.get("page_url"),
                        "user_agent": ua,
                        "meta": {"engine": ("openai" if agent._llm_client else "error"), "escalate": escalate},
                    }
                ],
            )
        except Exception:
            logger.exception("Failed to persist reply_init event (fn)")

        yield sse("init", init_payload)

        full_reply: str = ""
        stream_start = time.perf_counter()
        first_token_sent = False

        # Stream via OpenAI when configured; otherwise return error text
        if agent._llm_client is not None:
            try:
                system = agent._system_prompt(req.get("participant_group"))
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
                        if not first_token_sent:
                            first_token_sent = True
                            try:
                                from server.app.storage import SupabaseStore
                                ttft_ms = int((time.perf_counter() - stream_start) * 1000)
                                SupabaseStore().insert_rows(
                                    "interaction_events",
                                    [
                                        {
                                            "session_id": sid,
                                            "participant_group": req.get("participant_group"),
                                            "participant_id": req.get("participant_id"),
                                            "event": "first_token",
                                            "component": "chat_stream",
                                            "label": "first_token",
                                            "value": str(ttft_ms),
                                            "duration_ms": ttft_ms,
                                            "client_ts": datetime.now(timezone.utc).isoformat(),
                                            "page_url": req.get("page_url"),
                                            "user_agent": ua,
                                            "meta": None,
                                        }
                                    ],
                                )
                            except Exception:
                                logger.exception("Failed to persist first_token event (fn)")
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
        # Server-side telemetry: reply_done
        try:
            from server.app.storage import SupabaseStore
            total_ms = int((time.perf_counter() - stream_start) * 1000) if stream_start else None
            SupabaseStore().insert_rows(
                "interaction_events",
                [
                    {
                        "session_id": sid,
                        "participant_group": req.get("participant_group"),
                        "participant_id": req.get("participant_id"),
                        "event": "reply_done",
                        "component": "chat_stream",
                        "label": "stream_done",
                        "value": f"chars={len(full_reply)}",
                        "duration_ms": total_ms,
                        "client_ts": datetime.now(timezone.utc).isoformat(),
                        "page_url": req.get("page_url"),
                        "user_agent": ua,
                        "meta": {"chars": len(full_reply)},
                    }
                ],
            )
        except Exception:
            logger.exception("Failed to persist reply_done event (fn)")
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
