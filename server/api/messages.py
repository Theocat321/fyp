from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from server.app.storage import SupabaseStore

app = FastAPI(title="VodaCare Data API (messages)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = SupabaseStore()


@app.post("/")
@app.post("/api/messages")
def insert_message(m: dict):
    row = {
        "session_id": m.get("session_id"),
        "role": m.get("role"),
        "content": m.get("content"),
        "participant_id": m.get("participant_id"),
        "participant_name": m.get("participant_name"),
        "participant_group": m.get("participant_group"),
    }
    if not row["session_id"] or not row["role"] or row["content"] is None:
        return JSONResponse({"error": "missing_fields"}, status_code=400)
    stored, code = store.insert_rows("messages", [row])
    status = 200 if stored else (code if code else 202)
    return JSONResponse({"ok": True, "stored": stored}, status_code=status)


@app.get("/")
@app.get("/api/messages")
def get_messages(session_id: str):
    rows, code = store.select_rows(
        "messages",
        {"session_id": session_id},
        select="session_id,role,content,participant_id,participant_name,participant_group,created_at",
        order="created_at.asc",
        limit=200,
    )
    status = 200 if code and 200 <= code < 300 else (code or 500)
    return JSONResponse({"messages": rows}, status_code=status)
