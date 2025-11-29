# VodaCare Support (Next.js + Python on Vercel)

Local support chat for a mobile network provider.
Frontend is Next.js; backend is Python (FastAPI) deployed as Vercel Serverless Functions.

## Quick Start

- Prerequisites: Node.js 18+, Python 3.10+
- Ports: frontend `3000`, backend `8000`

1) Environment variables

- Use a single root `.env` for development (copy from `.env.example`). Both apps load it automatically.
- On Vercel, set env vars in the project settings. For local parity, from `web/` run `npm run env:pull` to create/update `web/.env.local`.

2) Backend (FastAPI)

- From `server/` (local dev):
  - Create venv and install: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
  - Run API: `uvicorn app.main:app --reload --port 8000`
  - Next.js proxies `/api/chat*` to this server in dev; in production, Python runs as Vercel functions in `api/`.

3) Frontend (Next.js)

- From `web/`:
  - Install deps: `npm install`
  - Run dev server: `npm run dev`
  - Open: `http://localhost:3000`

## Features

- Telco intents: plans, upgrades, data/balance, roaming, billing, coverage, support
- Quick‑reply suggestions
- Rule‑based by default; optional OpenAI replies
- Streaming replies via SSE (`/api/chat-stream`) served by Python in prod and proxied in dev
- Optional Supabase persistence and interaction logging
- Simple pre‑chat enrollment (name + group A/B)

## Configuration

- Frontend reads `NEXT_PUBLIC_API_BASE_URL` to call the backend
- Frontend streaming toggle: set `NEXT_PUBLIC_USE_STREAMING=true` to stream replies
- Backend reads `PROVIDER_NAME` and `ALLOWED_ORIGINS`

### OpenAI (optional)

- To enable LLM-generated replies, set in root `.env` (dev) or Vercel envs (prod):
  - `OPENAI_API_KEY=...`
  - `OPENAI_MODEL=gpt-4o-mini` (or preferred)
  - `OPENAI_BASE_URL=` (optional, e.g., for proxies/Azure)
- When set, replies come from the model; suggestions stay local.

### Assistant mode

- Control how narrow or open‑ended the assistant feels with `ASSISTANT_MODE`:
  - `open` (default): general chat is allowed; telecom topics are still supported.
  - `strict`: restricts behavior and suggestions to telecom/help topics.
- Set `ASSISTANT_MODE=open` in root `.env` for dev or in Vercel envs for production.

### Streaming (SSE)

- Endpoint: `POST /api/chat-stream`
- Request body: `{ "message": string, "session_id?": string }`
- Server sends SSE events:
  - `event: init` with `{ session_id, suggestions, topic, escalate }`
  - `event: token` with partial text tokens
  - `event: done` with `{ reply }`
- Frontend: set `NEXT_PUBLIC_USE_STREAMING=true` to use streaming path; falls back to non-streaming `/api/chat` otherwise.

### Supabase (optional)

- To persist messages from the frontend, set in `web/.env.local`:
  - `NEXT_PUBLIC_SUPABASE_URL=...`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY=...`
- Create tables (example schemas):
  - `participants`
    - `participant_id`: text primary key
    - `created_at`: timestamp with time zone default now()
    - `name`: text
    - `group`: text check in ('A','B')
    - `session_id`: text (optional)
  - `messages`
    - `id`: bigint PK (generated)
    - `created_at`: timestamp with time zone default now()
    - `session_id`: text
    - `role`: text check in ('user','assistant')
    - `content`: text
    - `participant_id`: text (optional FK to participants.participant_id)
    - `participant_name`: text (optional)
    - `participant_group`: text (optional)
- RLS: allow inserts for `anon` if desired for local dev, e.g. a permissive policy:
  - `create policy "allow anon inserts messages" on messages for insert to anon using (true) with check (true);`
  - `create policy "allow anon inserts participants" on participants for insert to anon using (true) with check (true);`
  - `create table if not exists interactions (id bigserial primary key, created_at timestamptz default now(), "group" text check ("group" in ('A','B')), input text, output text);`
  - `alter table interactions enable row level security;`
  - `create policy "allow anon inserts interactions" on interactions for insert to anon using (true) with check (true);`
- Notes: Frontend persistence is best‑effort; the UI works without it.

### Verbose interaction events (optional)

For detailed user behavior logs (component clicks, typing duration, message send timestamps, etc.), use the provided API route and table schema:

- API route: `POST /api/interaction`
  - Accepts a single event or an array. Minimal shape:
    - `session_id` string (required)
    - `event` string (e.g., `click`, `typing`, `message_send`)
    - Optional: `component`, `label`, `duration_ms`, `client_ts`, `page_url`, `participant_id`, `participant_group`, `meta`
- Server env (in `web/.env.local`):
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY` (server-only)
- Table DDL: see `res/verbose_interactions.sql` (creates `interaction_events` with useful indexes)

Client instrumentation in `web/components/ChatWindow.tsx` logs:
- text input focus/blur
- typing duration on submit
- suggestion chip clicks
- send button click and message send

If `SUPABASE_*` server vars are not set, events are accepted but not stored (returns 202).

## Project Structure

- `server/` FastAPI app and chatbot logic
- `web/` Next.js app with chat UI

## Deployment

- Single Vercel project from the repo root using `vercel.json`.
- Next.js app lives in `web/`. Python Serverless Functions live in `api/` and include shared logic from `server/app/*`.

### Unified Env (Dev + Vercel)

- Single file in dev: put your variables in the repo root `.env`. Both the Next.js app and the FastAPI server load it automatically in development.
- On Vercel: set envs in the dashboard (source of truth). For local dev, from `web/` run `npm run env:pull` to create/update `web/.env.local`.
- Do not set `NEXT_PUBLIC_API_BASE_URL` on Vercel; leave it empty so the UI calls the built‑in routes.
- Keep secrets out of Git: `.env` is git‑ignored; `web/.env` is ignored too.

## Notes

- In‑memory by default; restarting the API clears history.
- Local dev setup only.
