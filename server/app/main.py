from fastapi import FastAPI, Request
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import asyncio
import json
from typing import AsyncGenerator

from .config import get_allowed_origins, get_provider_name
from .models import ChatRequest, ChatResponse, InteractionEvent, ParticipantInsert, MessageInsert
from .agent import SupportAgent
from .storage import SupabaseStore


app = FastAPI(title="VodaCare Support API", version="0.1.0")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = SupportAgent()
store = SupabaseStore()


@app.get("/api/health")
def health():
    return {"status": "ok", "provider": get_provider_name()}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = agent.chat(req.message, req.session_id)
    return JSONResponse(result)


@app.post("/api/interaction")
async def interaction(req: Request):
    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"error": "invalid_json"}, status_code=400)

    # Accept single event, array, or {events: []}
    if isinstance(body, dict) and "events" in body and isinstance(body["events"], list):
        events_raw = body["events"]
    elif isinstance(body, list):
        events_raw = body
    else:
        events_raw = [body]

    events: list[InteractionEvent] = []
    for e in events_raw:
        try:
            events.append(InteractionEvent(**e))
        except Exception:
            continue
    if not events:
        # Accept but skip storing if no valid events (e.g., missing session_id)
        return JSONResponse({"ok": True, "stored": 0, "skipped": len(events_raw)}, status_code=202)

    # Route compact interaction ({group,input,output}) to 'interactions' table if present
    if len(events_raw) == 1 and isinstance(events_raw[0], dict) and {
        "group",
        "input",
        "output",
    }.issubset(set(events_raw[0].keys())):
        rows = [
            {
                "group": str(events_raw[0].get("group"))[:2],
                "input": str(events_raw[0].get("input"))[:4000],
                "output": str(events_raw[0].get("output"))[:4000],
            }
        ]
        # Debug log to help diagnose empty tables
        try:
            logger.info("/api/interaction compact rows=%d configured=%s", len(rows), store.is_configured())
        except Exception:
            pass
        stored, code = store.insert_rows("interactions", rows)
        status = 200 if stored else (code if code else 202)
        return JSONResponse({"ok": True, "stored": stored}, status_code=status)

    # Otherwise log verbose to interaction_events
    rows = []
    for e in events:
        rows.append(
            {
                "session_id": e.session_id,
                "participant_id": e.participant_id,
                "participant_group": e.participant_group,
                "event": (e.event or "unknown")[:64],
                "component": (e.component or None),
                "label": (e.label or None),
                "value": (e.value or None),
                "duration_ms": int(e.duration_ms) if e.duration_ms is not None else None,
                "client_ts": e.client_ts,
                "page_url": e.page_url,
                "user_agent": e.user_agent,
                "meta": e.meta,
            }
        )
    try:
        logger.info("/api/interaction verbose rows=%d configured=%s", len(rows), store.is_configured())
    except Exception:
        pass
    stored, code = store.insert_rows("interaction_events", rows)
    status = 200 if stored else (code if code else 202)
    if stored:
        return JSONResponse({"ok": True, "stored": stored}, status_code=status)
    return JSONResponse({"ok": True, "stored": 0, "skipped": len(rows)}, status_code=status)


@app.post("/api/participants")
def create_or_update_participant(p: ParticipantInsert):
    # If we only have participant_id + session_id, update session_id without touching name/group
    if p.participant_id and not p.name and not p.group and p.session_id:
        updated, code = store.update_by_pk(
            "participants", "participant_id", p.participant_id, {"session_id": p.session_id}
        )
        status = 200 if updated else (code if code else 202)
        return JSONResponse({"ok": True, "updated": updated}, status_code=status)

    row = {
        "participant_id": p.participant_id,
        "name": (p.name or None),
        "group": (p.group or None),
        "session_id": (p.session_id or None),
    }
    stored, code = store.insert_rows(
        "participants", [row], upsert=True, on_conflict="participant_id"
    )
    status = 200 if stored else (code if code else 202)
    return JSONResponse({"ok": True, "stored": stored}, status_code=status)


@app.post("/api/messages")
def insert_message(m: MessageInsert):
    row = {
        "session_id": m.session_id,
        "role": m.role,
        "content": m.content,
        "participant_id": m.participant_id,
        "participant_name": m.participant_name,
        "participant_group": m.participant_group,
    }
    stored, code = store.insert_rows("messages", [row])
    status = 200 if stored else (code if code else 202)
    return JSONResponse({"ok": True, "stored": stored}, status_code=status)


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

        # Determine topic + escalate; suggestions removed
        topic = agent._detect_topic(req.message)
        suggestions: list[str] = []
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
                messages.append({"role": "user", "content": req.message})

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
                        await asyncio.sleep(0)  # let event loop flush
            except Exception:
                logger.exception("OpenAI streaming failed")
                # Error text when LLM streaming fails
                reply = "There’s a problem — the chat service isn’t working right now. Please try again later."
                for part in _chunk_text_for_stream(reply):
                    full_reply += part
                    yield sse("token", part)
                    await asyncio.sleep(0)
        else:
            # No LLM configured: send error text
            logger.warning("LLM client not configured; sending error text in stream")
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
            "X-Accel-Buffering": "no",  # for proxies like nginx
        },
    )
