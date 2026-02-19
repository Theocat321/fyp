# Architecture

**Analysis Date:** 2026-02-19

## Pattern Overview

**Overall:** Microservices with independent frontend (Next.js) and backend (FastAPI)

**Key Characteristics:**
- Client-server separation with independent deployment targets
- API-first communication over HTTP/SSE
- Research-grade telemetry and feedback collection baked into the UX
- Support for two experimental conditions (participant groups A/B)
- Scenario-based roleplay testing for evaluation
- Pluggable LLM provider (OpenAI with fallback to rule-based)
- Supabase for persistent data storage (optional but recommended)

## Layers

**Frontend (Next.js 14, TypeScript):**
- Purpose: User-facing chat UI with research enrollment and feedback collection
- Location: `/Users/stagcto/fyp/web/`
- Contains: React components, API client, telemetry helpers, CSS
- Depends on: Next.js, React, Supabase client, browser APIs
- Used by: End users in browser

**Frontend API Routes (Next.js):**
- Purpose: Server-side proxies for sensitive operations (Supabase writes, feedback submission)
- Location: `/Users/stagcto/fyp/web/app/api/`
- Contains: POST/GET handlers for feedback, scenario data
- Depends on: Supabase SDK, environment variables
- Used by: Client-side chat logic

**Backend API (FastAPI, Python):**
- Purpose: Chat message processing, LLM invocation, research data persistence
- Location: `/Users/stagcto/fyp/server/app/`
- Contains: FastAPI app, support agent, storage adapter, models
- Depends on: OpenAI SDK, Supabase REST API, Pydantic for validation
- Used by: Frontend via HTTP (non-streaming) and Server-Sent Events (streaming)

**Storage Layer (Supabase):**
- Purpose: Persistent database for messages, participants, feedback, interaction events
- Location: Remote (env-configured via `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`)
- Contains: Tables for `messages`, `participants`, `support_feedback`, `interaction_events`
- Depends on: PostgreSQL backend, REST API
- Used by: Backend (via `SupabaseStore`), frontend (direct writes in some routes)

## Data Flow

**Chat Message Flow (Streaming):**

1. User types in `/Users/stagcto/fyp/web/components/ChatWindow.tsx`, presses Send
2. Message logged locally via `logEvent()` to `/api/interaction` endpoint
3. User message stored in Supabase via backend `/api/messages` (best-effort)
4. Message sent to backend `POST /api/chat-stream` with session_id, participant_group
5. Backend's `chat_stream()` in `/Users/stagcto/fyp/server/app/main.py`:
   - Ensures session exists via `agent._ensure_session()`
   - Records user message in `agent.sessions[sid]`
   - Detects topic via `agent._detect_topic()`
   - Sends SSE init event with metadata
   - Streams tokens from OpenAI via `agent._llm_client.chat.completions.create()`
   - Logs server-side telemetry for `reply_init`, `first_token`, `reply_done`
   - Appends assistant reply to session history
   - Yields final `done` event with complete reply
6. Frontend collects tokens in `onToken()` callback, formats with `formatStreamingText()`
7. Assistant message displayed and persisted to Supabase

**Feedback Submission:**

1. User clicks Finish button → sets `showFeedback = true`
2. Feedback form collects ratings (5-point scale) and optional comments
3. User submits → payload sent to `POST /api/feedback` (Next.js route)
4. Route uses Supabase client to insert into `support_feedback` table
5. Returns success/error to client
6. Client clears session from localStorage and redirects to home (enrollment form)

**Participant & Session Management:**

1. User submits enrollment form with name + group (A or B)
2. Form saved to localStorage (`vc_participant_name`, `vc_participant_group`, etc.)
3. Participant ID generated (UUID or random hex)
4. Session ID generated (UUID)
5. Participant upserted via `POST /api/participants` → backend writes to Supabase
6. On first message send, session confirmed with metadata
7. Subsequent messages within same session reuse session_id from localStorage

**State Management:**

- **Frontend local state:** Participant info, session ID, scenario context, feedback form values in React component state
- **Frontend persistent state:** Participant ID, session ID, scenario ID in `localStorage` (with prefix `vc_`)
- **Backend in-memory:** Chat history per session in `agent.sessions: Dict[str, List[Tuple[str, str]]]`
- **Remote state:** All persistent data in Supabase (messages, feedback, interaction events)

## Key Abstractions

**SupportAgent:**
- Purpose: Encapsulates chat logic, topic detection, knowledge base, and LLM interaction
- Examples: `/Users/stagcto/fyp/server/app/agent.py`
- Pattern: Stateful object with in-memory session tracking and optional OpenAI integration

**SupabaseStore:**
- Purpose: REST API adapter for Supabase (insert, update, select rows)
- Examples: `/Users/stagcto/fyp/server/app/storage.py`
- Pattern: Wrapper around `requests` library with retry-safe semantics; treats missing config as graceful degradation

**ChatWindow Component:**
- Purpose: Main React component encapsulating enrollment UI, chat history, message input, and feedback modal
- Examples: `/Users/stagcto/fyp/web/components/ChatWindow.tsx`
- Pattern: Container component managing complex state machine (not-started → chat active → feedback pending → done)

**API Models (Pydantic):**
- Purpose: Type-safe request/response validation
- Examples: `/Users/stagcto/fyp/server/app/models.py` (`ChatRequest`, `ChatResponse`, `InteractionEvent`, `FeedbackInsert`)
- Pattern: All incoming JSON validated against models; prevents unexpected fields

## Entry Points

**Frontend:**
- Location: `/Users/stagcto/fyp/web/app/page.tsx`
- Triggers: Browser navigation to `https://{host}/`
- Responsibilities: Renders root layout with app header + ChatWindow component

**Backend:**
- Location: `/Users/stagcto/fyp/server/app/main.py`
- Triggers: `uvicorn server.app.main:app --host 0.0.0.0 --port 8000`
- Responsibilities: FastAPI app initialization, middleware setup (CORS), router registration, health checks

**Streaming Endpoint:**
- Location: `/Users/stagcto/fyp/server/app/main.py` → `chat_stream()` function
- Triggers: `POST /api/chat-stream` with `ChatRequest` body
- Responsibilities: Async event generation, SSE formatting, OpenAI integration, telemetry logging

**Feedback API:**
- Location: `/Users/stagcto/fyp/web/app/api/feedback/route.ts`
- Triggers: `POST /api/feedback` from frontend form
- Responsibilities: Validate body, write to Supabase, return success/error

## Error Handling

**Strategy:** Graceful degradation with best-effort logging

**Patterns:**

- **Telemetry:** All `logEvent()` calls wrapped in try-catch; swallowed on failure (line 44-46 in `/Users/stagcto/fyp/web/lib/telemetry.ts`)
- **Storage writes:** Backend returns success status even if Supabase insert fails (line 104 in `/Users/stagcto/fyp/server/app/main.py`)
- **LLM failure:** Falls back to static error text when OpenAI unavailable (lines 374-389 in `/Users/stagcto/fyp/server/app/main.py`)
- **Optional config:** LLM client init failure logs but doesn't crash (lines 31-42 in `/Users/stagcto/fyp/server/app/agent.py`)
- **Frontend:** Missing session/participant state generates new IDs on-demand (lines 138-156 in `/Users/stagcto/fyp/web/components/ChatWindow.tsx`)

## Cross-Cutting Concerns

**Logging:**
- Frontend: `console.error()` for debugging; structured events via `/api/interaction`
- Backend: Python `logging` module; warnings logged for storage diagnostics

**Validation:**
- Backend: Pydantic models enforce type and required field validation
- Frontend: Client-side form validation for enrollment (name required, group required)

**Authentication:**
- None; system is public (research condition: participant info self-reported)
- Supabase uses service role key for backend writes (environment-protected)

**Telemetry:**
- Captured via `InteractionEvent` schema (session_id, participant_id, participant_group, event type, component, label, value, duration_ms, client_ts)
- Sent client-side to `/api/interaction` endpoint
- Logged server-side for reply init, first token, reply done

**Session Isolation:**
- Each session has unique session_id (UUID)
- Messages grouped by session_id in both in-memory (agent.sessions) and Supabase (messages table)
- No cross-session message leakage

---

*Architecture analysis: 2026-02-19*
