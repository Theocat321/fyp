# VodaCare Support Chatbot (Next.js + FastAPI)

A local full‑stack customer support chatbot specialized for a mobile network provider (think Vodafone). Frontend is Next.js, backend is FastAPI. No production setup — local dev only.

## Quick Start

- Prerequisites: Node.js 18+, Python 3.10+
- Ports: frontend `3000`, backend `8000`

1) Copy env files

- Root example: `.env.example`
- Recommended copies:
  - `cp server/.env.example server/.env`
  - `cp web/.env.example web/.env.local`

2) Backend (FastAPI)

- From `server/`:
  - Create venv and install: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
  - Run API: `uvicorn app.main:app --reload --port 8000`

3) Frontend (Next.js)

- From `web/`:
  - Install deps: `npm install`
  - Run dev server: `npm run dev`
  - Open: `http://localhost:3000`

## Features

- Mobile telco–themed chatbot with friendly tone
- Common intents: plans, upgrades, data/balance, roaming, billing, coverage, support
- Suggestions (quick replies) returned by API and shown as chips
- Rule-based agent by default; optional OpenAI-powered replies when configured
- Streaming replies via SSE when using the new `/api/chat-stream` endpoint
- Optional Supabase integration to persist chat messages

## Configuration

- Frontend reads `NEXT_PUBLIC_API_BASE_URL` to call the backend
- Frontend streaming toggle: set `NEXT_PUBLIC_USE_STREAMING=true` to stream replies
- Backend reads `PROVIDER_NAME` and `ALLOWED_ORIGINS`

### Optional: OpenAI SDK

- To enable LLM-generated replies, set in `server/.env`:
  - `OPENAI_API_KEY=...`
  - `OPENAI_MODEL=gpt-4o-mini` (or preferred)
  - `OPENAI_BASE_URL=` (optional, e.g., for proxies/Azure)
- When `OPENAI_API_KEY` is set, the API uses the model for reply text while keeping suggestions and guardrails locally.

### Streaming Chat (SSE)

- Endpoint: `POST /api/chat-stream`
- Request body: `{ "message": string, "session_id?": string }`
- Server sends SSE events:
  - `event: init` with `{ session_id, suggestions, topic, escalate }`
  - `event: token` with partial text tokens
  - `event: done` with `{ reply }`
- Frontend: set `NEXT_PUBLIC_USE_STREAMING=true` to use streaming path; falls back to non-streaming `/api/chat` otherwise.

### Optional: Supabase

- To persist messages from the frontend, set in `web/.env.local`:
  - `NEXT_PUBLIC_SUPABASE_URL=...`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY=...`
- Create a table `messages` (example schema):
  - `id`: bigint PK (generated)
  - `created_at`: timestamp with time zone default now()
  - `session_id`: text
  - `role`: text check in ('user','assistant')
  - `content`: text
- RLS: allow inserts for `anon` if desired for local dev, e.g. a permissive policy:
  - `create policy "allow anon inserts" on messages for insert to anon using (true) with check (true);`
- Notes: Frontend persistence is best-effort and non-blocking; if Supabase is not configured, the UI continues to function.

## Project Structure

- `server/` FastAPI app and chatbot logic
- `web/` Next.js app with chat UI

## Notes

- All data is in-memory; restarting the API clears session history.
- This is a local dev setup; no production configs included.
