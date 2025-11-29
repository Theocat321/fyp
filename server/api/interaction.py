from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from server.app.storage import SupabaseStore

app = FastAPI(title="VodaCare Data API (interaction)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = SupabaseStore()


@app.post("/")
async def interaction(req: Request):
    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"error": "invalid_json"}, status_code=400)

    if isinstance(body, dict) and "events" in body and isinstance(body["events"], list):
        events_raw = body["events"]
    elif isinstance(body, list):
        events_raw = body
    else:
        events_raw = [body]

    if not events_raw:
        return JSONResponse({"ok": True, "stored": 0, "skipped": 0}, status_code=202)

    # compact interaction
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
        try:
            import logging
            logging.getLogger(__name__).info("/api/interaction (fn) compact rows=%d configured=%s", len(rows), store.is_configured())
        except Exception:
            pass
        stored, code = store.insert_rows("interactions", rows)
        status = 200 if stored else (code if code else 202)
        return JSONResponse({"ok": True, "stored": stored}, status_code=status)

    rows = []
    for e in events_raw:
        if not isinstance(e, dict) or not e.get("session_id"):
            continue
        rows.append(
            {
                "session_id": e.get("session_id"),
                "participant_id": e.get("participant_id"),
                "participant_group": e.get("participant_group"),
                "event": (e.get("event") or "unknown")[:64],
                "component": e.get("component"),
                "label": e.get("label"),
                "value": e.get("value"),
                "duration_ms": e.get("duration_ms"),
                "client_ts": e.get("client_ts"),
                "page_url": e.get("page_url"),
                "user_agent": e.get("user_agent"),
                "meta": e.get("meta"),
            }
        )
    if not rows:
        return JSONResponse({"ok": True, "stored": 0, "skipped": len(events_raw)}, status_code=202)
    try:
        import logging
        logging.getLogger(__name__).info("/api/interaction (fn) verbose rows=%d configured=%s", len(rows), store.is_configured())
    except Exception:
        pass
    stored, code = store.insert_rows("interaction_events", rows)
    status = 200 if stored else (code if code else 202)
    if stored:
        return JSONResponse({"ok": True, "stored": stored}, status_code=status)
    return JSONResponse({"ok": True, "stored": 0, "skipped": len(rows)}, status_code=status)
