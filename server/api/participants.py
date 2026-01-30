from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from server.app.storage import SupabaseStore

app = FastAPI(title="VodaCare Data API (participants)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = SupabaseStore()


@app.post("/")
@app.post("/api/participants")
def upsert_participant(p: dict):
    pid = p.get("participant_id")
    if not pid:
        return JSONResponse({"error": "participant_id_required"}, status_code=400)
    name = p.get("name")
    group = p.get("group")
    session_id = p.get("session_id")
    # If only updating session_id for an existing participant, do a PATCH update
    if pid and not name and not group and session_id:
        updated, code = store.update_by_pk("participants", "participant_id", pid, {"session_id": session_id})
        status = 200 if updated else (code if code else 202)
        return JSONResponse({"ok": True, "updated": updated}, status_code=status)
    row = {
        "participant_id": pid,
        "name": name,
        "group": group,
        "session_id": session_id,
        "scenario_id": p.get("scenario_id"),
    }
    stored, code = store.insert_rows("participants", [row], upsert=True, on_conflict="participant_id")
    status = 200 if stored else (code if code else 202)
    return JSONResponse({"ok": True, "stored": stored}, status_code=status)
