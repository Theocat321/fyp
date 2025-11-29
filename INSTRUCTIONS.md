# Vercel Deployment

Single project deployment from the repo root. The Next.js app (in `web/`) serves the UI, and Python Serverless Functions (in `api/`) provide the chat backend. The shared chatbot logic lives in `server/app/*` and is bundled into the Python functions.

## Settings

- Root Directory: repository root (contains `vercel.json`)
- Frameworks: Next.js (UI) + Python (Serverless Functions)
- `vercel.json` wires builds and routes.

No `vercel.json` required.

## Env Vars

Client and API:

- `NEXT_PUBLIC_USE_STREAMING` = `true`

LLM (optional):

- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default `gpt-4o-mini`)
- `OPENAI_BASE_URL` (optional)
- `PROVIDER_NAME` (e.g., `VodaCare`)
- `ASSISTANT_MODE` = `open` | `strict`

Supabase (optional):

- Client: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- Server logging: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`

Leave `NEXT_PUBLIC_API_BASE_URL` unset so the UI uses relative `/api/*` which resolve to Python functions in production and proxy to FastAPI in local dev.

## Supabase Tables (optional)

Participants (`participants`):
- `participant_id` text PK
- `created_at` timestamptz default now()
- `name` text
- `group` text in ('A','B')
- `session_id` text (optional)

Messages (`messages`):
- `id` bigserial PK
- `created_at` timestamptz default now()
- `session_id` text
- `role` text in ('user','assistant')
- `content` text
- Optional: `participant_id`, `participant_name`, `participant_group`

Minimal interactions (`interactions`):

```
create table if not exists interactions (
  id bigserial primary key,
  created_at timestamptz default now(),
  "group" text check ("group" in ('A','B')),
  input text,
  output text
);
alter table interactions enable row level security;
create policy "allow anon inserts interactions" on interactions
for insert to anon using (true) with check (true);
```

Verbose events (server): see `res/verbose_interactions.sql` and POST `/api/interaction`.

## Streaming

- `POST /api/chat-stream` returns SSE (`text/event-stream`) from the Python function.
- With `OPENAI_API_KEY`, tokens stream from OpenAI; otherwise a rule‑based reply is chunked.
- The UI consumes tokens and updates the assistant bubble live.

## Local Dev

Single .env (recommended):

- Put all variables in the repo root `.env`. Both the Next.js app and the FastAPI server load it automatically in development.
- Alternatively, pull from Vercel into `web/.env.local`: `cd web && npm run env:pull`.

Local dev (proxy to FastAPI):

- Start FastAPI: `cd server && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000`
- Start Next.js: `cd web && npm install && npm run dev` then open http://localhost:3000
- Next.js rewrites `/api/chat*` to `http://localhost:8000` during dev, so the UI always calls `/api/*`.

## Notes

- Vercel functions are stateless; UI holds session state. Use Supabase to persist if needed.
