# External Integrations

**Analysis Date:** 2026-02-19

## APIs & External Services

**AI/Language Model:**
- OpenAI API - LLM-powered chat responses
  - SDK/Client: `openai` package (JS: 4.63.0, Python: >=1.42.0)
  - Auth: `OPENAI_API_KEY` environment variable
  - Model: `OPENAI_MODEL` (default: gpt-4o-mini)
  - Optional custom base URL: `OPENAI_BASE_URL`
  - Used by: `SupportAgent` in `/Users/stagcto/fyp/server/app/agent.py`, chat endpoints

## Data Storage

**Databases:**
- PostgreSQL (via Supabase)
  - Connection: Supabase REST API
  - URL: `SUPABASE_URL` environment variable
  - Auth: `SUPABASE_SERVICE_ROLE_KEY` (backend), `NEXT_PUBLIC_SUPABASE_ANON_KEY` (frontend)
  - Client:
    - JavaScript: `@supabase/supabase-js` 2.46.1 (browser and Node.js)
    - Python: Direct REST API via `requests` package
  - Tables accessed:
    - `support_feedback` - User feedback and ratings (see `/Users/stagcto/fyp/web/app/api/feedback/route.ts`)
    - `messages` - Chat message history
    - `participants` - Participant metadata
    - `interaction_events` - Detailed user interaction telemetry
  - Configuration in server: `/Users/stagcto/fyp/server/app/storage.py` implements `SupabaseStore` class with REST methods

**File Storage:**
- Local filesystem only - No S3 or cloud storage integration detected

**Caching:**
- In-memory session storage - `SupportAgent.sessions` dict in `/Users/stagcto/fyp/server/app/agent.py`
- No Redis or external cache detected

## Authentication & Identity

**Auth Provider:**
- None detected - Application uses anonymous Supabase access with public/service role keys
- No user authentication implemented
- Session identification via `session_id` parameter (UUID or custom identifier)

**Participant Tracking:**
- Participants tracked via `participant_id` and `participant_group` (A/B testing groups)
- No login/auth required

## Monitoring & Observability

**Error Tracking:**
- None detected

**Logs:**
- Python logging module (`logging.getLogger(__name__)`) in FastAPI backend
- Console logging in Next.js frontend
- Server-side telemetry via `interaction_events` table:
  - `reply_init` - Stream initialization
  - `first_token` - Time-to-first-token metric
  - `reply_done` - Stream completion with character count
- See `/Users/stagcto/fyp/server/app/main.py` for event recording

**Diagnostics:**
- Health check endpoint: `GET /api/health` returns Supabase configuration status
- Config logging in feedback endpoint: `/api/feedback` logs Supabase connection diagnostics

## CI/CD & Deployment

**Hosting:**
- Vercel platform (primary deployment)
- Can also run standalone FastAPI backend on any server

**CI Pipeline:**
- None detected - No GitHub Actions or CI config files found

**Build & Deployment Configuration:**
- `vercel.json` at root defines:
  - Next.js app build: `web/package.json` → `@vercel/next`
  - Python serverless functions: `server/api/**/*.py` → `@vercel/python`
  - Route mapping for API endpoints to Python functions or Next.js routes

## Environment Configuration

**Required env vars (production):**
- `OPENAI_API_KEY` - Required for LLM features
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Server-side Supabase access
- `NEXT_PUBLIC_SUPABASE_URL` - Browser-side Supabase (can differ from server)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Browser-side Supabase access

**Optional but recommended:**
- `OPENAI_BASE_URL` - Custom LLM endpoint (e.g., Azure OpenAI)
- `PROVIDER_NAME` - Brand name for responses (default: VodaCare)
- `ASSISTANT_MODE` - "open" for flexible, "strict" for policy-aligned (default: open)

**Secrets location:**
- `.env` file in repository root (not committed to git)
- Vercel Project Settings → Environment Variables (for production)
- See `.env.example` for template

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- None detected

## Data Flow

**Chat Request Flow:**
1. Browser sends POST `/api/chat-stream` with message and session_id
2. Next.js routes to Python backend `/api/chat-stream` (dev mode) or Vercel function (production)
3. `SupportAgent` processes message via OpenAI API
4. Response streamed back as Server-Sent Events (SSE) with tokens
5. Telemetry recorded in `interaction_events` table (reply_init, first_token, reply_done)
6. Message history stored in `messages` table

**Feedback Submission Flow:**
1. Browser sends POST `/api/feedback` with form data and session_id
2. Next.js API route (`/Users/stagcto/fyp/web/app/api/feedback/route.ts`) validates and inserts to `support_feedback` table
3. Feedback stored with ratings, participant metadata, and interaction metrics

**Interaction Events:**
- Recorded via POST `/api/interaction` with batch of events
- Events include component, duration, user_agent, page_url
- Stored in `interaction_events` table for analysis

---

*Integration audit: 2026-02-19*
