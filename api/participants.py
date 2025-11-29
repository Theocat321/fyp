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
def upsert_participant(p: dict):
    row = {
        "participant_id": p.get("participant_id"),
        "name": p.get("name"),
        "group": p.get("group"),
        "session_id": p.get("session_id"),
    }
    if not row["participant_id"]:
        return JSONResponse({"error": "participant_id_required"}, status_code=400)
    stored, code = store.insert_rows("participants", [row], upsert=True)
    status = 200 if stored else (code if code else 202)
    return JSONResponse({"ok": True, "stored": stored}, status_code=status)

