# Codebase Structure

**Analysis Date:** 2026-02-19

## Directory Layout

```
/Users/stagcto/fyp/
├── web/                      # Next.js frontend (TypeScript)
│   ├── app/
│   │   ├── page.tsx          # Root page (renders ChatWindow)
│   │   ├── layout.tsx        # Root layout (header, app-shell)
│   │   └── api/
│   │       ├── feedback/     # POST /api/feedback (Supabase writes)
│   │       └── scenarios/    # GET /api/scenarios (scenario list)
│   ├── components/           # React components
│   │   ├── ChatWindow.tsx    # Main chat UI container (790 lines)
│   │   ├── MessageBubble.tsx # Message display helper
│   │   └── Markdown.tsx      # Markdown rendering
│   ├── lib/                  # Shared TypeScript utilities
│   │   ├── api.ts           # Chat API client (sendMessage, sendMessageStream, fetchMessages)
│   │   ├── agent.ts         # Topic detection, knowledge base, agent helpers
│   │   ├── telemetry.ts     # Event logging (logEvent)
│   │   ├── supabaseClient.ts # Public anon client
│   │   └── supabaseAdmin.ts  # Service role client (unused in current flow)
│   ├── styles/              # Global CSS
│   │   └── globals.css
│   ├── package.json         # Node.js dependencies (Next.js, React, Supabase)
│   ├── tsconfig.json        # TypeScript config (strict mode)
│   └── next.config.mjs      # Next.js config
│
├── server/                   # FastAPI backend (Python)
│   ├── app/
│   │   ├── main.py          # FastAPI app, routers, chat endpoints
│   │   ├── agent.py         # SupportAgent (chat logic, LLM integration)
│   │   ├── storage.py       # SupabaseStore (REST API adapter)
│   │   ├── config.py        # Environment variable loaders
│   │   └── models.py        # Pydantic models (ChatRequest, FeedbackInsert, etc.)
│   ├── api/                 # API route modules (deprecated, moved to main.py)
│   │   ├── chat.py
│   │   ├── chat_stream.py
│   │   ├── scenarios.py     # GET /api/scenarios router
│   │   ├── interaction.py
│   │   ├── messages.py
│   │   └── participants.py
│   ├── migrations/          # (Not used; schema managed in Supabase)
│   ├── requirements.txt     # Python dependencies (fastapi, uvicorn, openai)
│   ├── __init__.py
│   └── venv/               # Python virtual environment
│
├── llm-testing/             # LLM evaluation framework (separate project)
│   ├── src/                # Python evaluation code
│   ├── data/               # Scenario and persona definitions
│   └── config/             # Test configuration
│
├── res/                     # Resource files
│   └── personas/           # Persona definitions (for testing)
│
├── docs/                   # Documentation
│   └── plans/             # GSD planning documents
│
├── .planning/              # GSD mapping documents
│   └── codebase/          # Generated analysis (this file)
│
├── .env                    # Environment variables (shared between web and server)
├── .env.example            # Template for environment vars
├── vercel.json             # Vercel deployment config
├── README.md               # Project overview
└── DESIGN.md              # Design document (product spec)
```

## Directory Purposes

**`web/app/`**
- Purpose: Next.js app directory (Next.js 14 app router)
- Contains: Page components, API routes
- Key files: `page.tsx` (entry point), `layout.tsx` (root layout), `api/feedback/route.ts`, `api/scenarios/route.ts`

**`web/components/`**
- Purpose: Reusable React components
- Contains: ChatWindow (main container), MessageBubble (display), Markdown (rendering)
- Key files: `ChatWindow.tsx` (790 lines, handles entire flow)

**`web/lib/`**
- Purpose: Shared TypeScript utilities and adapters
- Contains: API client, telemetry, agent helpers, Supabase clients
- Key files: `api.ts` (REST client), `agent.ts` (topic detection), `telemetry.ts` (event logging)

**`web/styles/`**
- Purpose: Global CSS
- Contains: CSS for app-shell, chat UI, forms, feedback modal
- Key files: `globals.css`

**`server/app/`**
- Purpose: FastAPI application core
- Contains: Main app, agent logic, storage adapter, config
- Key files: `main.py` (app + routers), `agent.py` (SupportAgent class), `storage.py` (Supabase adapter)

**`server/api/`**
- Purpose: Legacy API module structure (mostly superseded by main.py)
- Contains: Individual endpoint modules
- Key files: `scenarios.py` (registered as `/api/scenarios` router)

**`llm-testing/`**
- Purpose: Separate LLM evaluation framework
- Contains: Python code for automated evaluation, scenario definitions, persona data
- Key files: `src/` (evaluator, experiment orchestrator), `data/scenarios/`, `data/personas/`

**`docs/`**
- Purpose: Project documentation
- Contains: GSD planning documents and design specs
- Key files: `plans/` (generated phase docs)

## Key File Locations

**Entry Points:**

| File | Purpose | Trigger |
|------|---------|---------|
| `/Users/stagcto/fyp/web/app/page.tsx` | Root page component | Browser → `/` |
| `/Users/stagcto/fyp/web/app/layout.tsx` | Root layout | Wraps all pages |
| `/Users/stagcto/fyp/server/app/main.py` | FastAPI app | `uvicorn server.app.main:app` |

**Configuration:**

| File | Purpose |
|------|---------|
| `/Users/stagcto/fyp/.env` | Environment variables (API keys, Supabase URL) |
| `/Users/stagcto/fyp/web/tsconfig.json` | TypeScript compiler config |
| `/Users/stagcto/fyp/web/next.config.mjs` | Next.js build config |
| `/Users/stagcto/fyp/server/app/config.py` | Python environment loaders |

**Core Logic:**

| File | Purpose | Lines |
|------|---------|-------|
| `/Users/stagcto/fyp/web/components/ChatWindow.tsx` | Main chat UI + state machine | 790 |
| `/Users/stagcto/fyp/server/app/agent.py` | LLM integration + topic detection | ~200 |
| `/Users/stagcto/fyp/server/app/main.py` | FastAPI app + endpoints | ~445 |
| `/Users/stagcto/fyp/web/lib/api.ts` | Chat client (sendMessage, streaming) | 141 |

**Models & Validation:**

| File | Purpose |
|------|---------|
| `/Users/stagcto/fyp/server/app/models.py` | Pydantic schemas (ChatRequest, FeedbackInsert, etc.) |
| `/Users/stagcto/fyp/web/lib/agent.ts` | Topic detection, knowledge base |
| `/Users/stagcto/fyp/web/lib/telemetry.ts` | Event schema (InteractionEvent) |

**Telemetry & Storage:**

| File | Purpose |
|------|---------|
| `/Users/stagcto/fyp/web/lib/telemetry.ts` | Client-side event logging |
| `/Users/stagcto/fyp/server/app/storage.py` | Supabase REST adapter |
| `/Users/stagcto/fyp/server/app/config.py` | Env loaders for Supabase credentials |

## Naming Conventions

**Files:**

- React components: PascalCase with `.tsx` extension (e.g., `ChatWindow.tsx`, `MessageBubble.tsx`)
- Utilities: camelCase with `.ts` or `.tsx` extension (e.g., `api.ts`, `telemetry.ts`, `agent.ts`)
- API routes: `route.ts` in directory matching endpoint path (e.g., `app/api/feedback/route.ts` → `POST /api/feedback`)
- Python modules: snake_case with `.py` extension (e.g., `main.py`, `agent.py`, `models.py`)

**Directories:**

- Frontend: lowercase (e.g., `components/`, `lib/`, `styles/`)
- Backend: lowercase (e.g., `app/`, `api/`, `migrations/`)
- API routes: lowercase matching endpoint namespace (e.g., `app/api/feedback/`, `app/api/scenarios/`)

**Variables:**

- Frontend state: camelCase (e.g., `sessionId`, `participantName`, `showFeedback`)
- Functions: camelCase (e.g., `ensureSessionId()`, `onSend()`, `formatStreamingText()`)
- TypeScript types: PascalCase (e.g., `ChatResponse`, `InteractionEvent`, `Msg`)
- Python variables: snake_case (e.g., `session_id`, `participant_group`)

**Environment Variables:**

- Client-side public: `NEXT_PUBLIC_*` prefix (e.g., `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_SUPABASE_URL`)
- Server-side secrets: no prefix (e.g., `OPENAI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`)

## Where to Add New Code

**New Chat Feature:**
- UI logic: Add state + handlers to `ChatWindow.tsx` component state (lines 11-60)
- API integration: Add fetch/SSE handler in `lib/api.ts` (lines 25-128)
- Backend processing: Add endpoint to `/Users/stagcto/fyp/server/app/main.py` using FastAPI decorators

**New Component:**
- Create file in `/Users/stagcto/fyp/web/components/` with PascalCase name
- Example pattern: Import React hooks, define props type, export default function
- Use `"use client"` directive if component needs interactivity

**New API Endpoint:**
- For frontend-only proxy: Create `route.ts` in `/Users/stagcto/fyp/web/app/api/{endpoint}/`
- For backend endpoint: Add decorated function to `/Users/stagcto/fyp/server/app/main.py` (e.g., `@app.post("/api/...")`)
- Register routers via `app.include_router()` in main.py (line 35)

**New Utility Function:**
- Client: Add to appropriate file in `/Users/stagcto/fyp/web/lib/` (or create new file if substantial)
- Server: Add to `/Users/stagcto/fyp/server/app/` module

**New Database Table:**
- Schema: Manage in Supabase console (no migrations in codebase)
- Access: Add method to `SupabaseStore` class in `/Users/stagcto/fyp/server/app/storage.py`
- Validation: Add Pydantic model to `/Users/stagcto/fyp/server/app/models.py`

## Special Directories

**`web/node_modules/`**
- Purpose: Installed npm dependencies
- Generated: Yes (from `package-lock.json`)
- Committed: No (in `.gitignore`)

**`web/.next/`**
- Purpose: Next.js build output and cache
- Generated: Yes (from `next build` or dev server)
- Committed: No (in `.gitignore`)

**`server/venv/`**
- Purpose: Python virtual environment
- Generated: Yes (from `python -m venv venv`)
- Committed: No (in `.gitignore`)

**`.planning/codebase/`**
- Purpose: Generated codebase analysis documents (ARCHITECTURE.md, STRUCTURE.md, etc.)
- Generated: Yes (by `/gsd:map-codebase`)
- Committed: Yes (for future reference)

**`llm-testing/venv/`**
- Purpose: Separate Python venv for evaluation framework
- Generated: Yes
- Committed: No

---

*Structure analysis: 2026-02-19*
