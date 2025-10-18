# Vercel Deployment

Deploy only the Next.js app in `web/`. The FastAPI app in `server/` is for local experiments and isn’t needed on Vercel.

## Settings

- Root Directory: `web`
- Framework: Next.js
- Build: `npm run build`
- Install: `npm install`
- Output: `.next`

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

Leave `NEXT_PUBLIC_API_BASE_URL` unset so the UI uses built‑in routes (`/api/*`).

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

- `POST /api/chat-stream` returns SSE (`text/event-stream`).
- With `OPENAI_API_KEY`, tokens stream from OpenAI; otherwise a rule‑based reply is chunked.
- The UI consumes tokens and updates the assistant bubble live.

## Local Dev

Single .env (recommended):

- Put all variables in the repo root `.env`. Both the Next.js app and the FastAPI server load it automatically in development.
- Alternatively, pull from Vercel into `web/.env.local`: `cd web && npm run env:pull`.

Using Next.js API only:

- `cd web && npm install && npm run dev`
- Open http://localhost:3000

Using FastAPI (optional):

- Create venv, install, run uvicorn (see README)
- If you prefer routing UI to FastAPI, set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` in `.env`.

## Notes

- Vercel functions are stateless; UI holds session state. Use Supabase to persist if needed.
- The FastAPI app is optional for local use; Vercel uses the Next.js API.
