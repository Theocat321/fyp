# VodaCare Support Chat Platform - Design Document

**Project:** VodaCare Support
**Version:** 0.1.0
**Type:** Final Year Project (FYP) - Chatbot Platform with Human-LLM Testing Alignment
**Date:** 2024-2025

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Overview](#project-overview)
3. [Core Architecture](#core-architecture)
4. [Design Principles](#design-principles)
5. [System Components](#system-components)
6. [Frontend Design](#frontend-design)
7. [Backend Design](#backend-design)
8. [Data Model & Storage](#data-model--storage)
9. [API Design](#api-design)
10. [LLM Integration & Streaming](#llm-integration--streaming)
11. [Testing Framework](#testing-framework)
12. [Deployment Architecture](#deployment-architecture)
13. [Configuration & Environment Management](#configuration--environment-management)
14. [Data Flow & Interactions](#data-flow--interactions)
15. [Performance & Scalability](#performance--scalability)
16. [Security Design](#security-design)
17. [Error Handling & Resilience](#error-handling--resilience)
18. [Observability & Monitoring](#observability--monitoring)

---

## Executive Summary

VodaCare Support is a Next.js + Python FastAPI-based chat application that provides customer support for a mobile network provider (telecommunications domain). The system is designed to serve both rule-based and LLM-powered conversational responses, with optional data persistence via Supabase and comprehensive testing frameworks for evaluating both LLM-simulated and human-conducted interactions.

The platform uniquely combines:
- **Dual-mode operation:** Rule-based responses (default) with optional OpenAI LLM integration
- **Streaming architecture:** Server-Sent Events (SSE) for real-time token streaming
- **Human-LLM testing alignment:** Identical evaluation rubrics and scenarios for both automated and human testing
- **Research-focused design:** Built to support FYP research on LLM quality vs. human interactions
- **A/B testing infrastructure:** Support for variant testing with group-based participant allocation

The architecture follows a clear separation of concerns with the frontend serving as the UI layer, the Python FastAPI backend handling logic and LLM interactions, and Supabase providing optional persistence and telemetry collection.

---

## Project Overview

### Purpose

VodaCare Support is a customer support chatbot for a fictional mobile network provider. It addresses customer inquiries across multiple domains including plans, billing, roaming, network coverage, device management, and escalation to human support.

The platform is fundamentally designed as a research platform to explore the alignment between:
- Automated LLM-simulated customer interactions
- Real human customer interactions
- Quality evaluation methodologies for both

### Scope

**In Scope:**
- Chat interface with message history
- Rule-based intent detection and response generation
- Optional OpenAI LLM integration for generated responses
- Server-Sent Events (SSE) streaming for real-time response tokens
- Participant enrollment and session management
- Detailed interaction event logging (telemetry)
- Supabase integration for data persistence
- Feedback collection with rubric-aligned ratings
- Scenario-guided testing framework
- Human-LLM evaluation comparison

**Out of Scope:**
- User authentication (simplified participant ID model)
- Real phone/account verification
- Payment processing
- Actual network management APIs
- Mobile app (web-only)
- Complex business logic beyond telecom domain

### Key Stakeholders

- **End Users:** Customers seeking support (both test participants and real users)
- **Researchers:** FYP students evaluating LLM vs. human performance
- **Administrators:** Operations team configuring the system and analyzing results
- **LLM Providers:** OpenAI (for optional LLM responses)

---

## Core Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER (Web Browser)                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              Next.js Frontend Application (React 18)              │   │
│  │  - Chat UI with message history                                  │   │
│  │  - Participant enrollment form                                   │   │
│  │  - Scenario selection interface                                  │   │
│  │  - Feedback form with rubric ratings                             │   │
│  │  - Session management                                            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└───────────────────────────┬────────────────────────────────────────────┘
                            │
                HTTP REST + SSE
                            │
        ┌───────────────────┴────────────────────┐
        │                                        │
┌───────▼──────────────┐          ┌─────────────▼──────────────┐
│   VERCEL EDGE LAYER  │          │   PYTHON SERVERLESS LAYER  │
│   (Next.js Routes)   │          │   (FastAPI Functions)      │
│                      │          │                            │
│  - Auth middleware   │          │  - /api/chat               │
│  - Request proxying  │          │  - /api/chat-stream (SSE)  │
│  - SSE tunneling     │          │  - /api/feedback           │
│  - Env var loading   │          │  - /api/messages           │
│                      │          │  - /api/participants       │
│                      │          │  - /api/interaction        │
│                      │          │  - /api/scenarios          │
└──────────────────────┘          └─────────────┬──────────────┘
                                                │
        ┌───────────────────────────────────────┤
        │                                       │
┌───────▼──────────────────┐      ┌────────────▼──────────┐
│  SUPABASE BACKEND        │      │  OPENAI API           │
│  (Optional Persistence)  │      │  (Optional LLM)       │
│                          │      │                       │
│  - Messages table        │      │  - Chat completions   │
│  - Participants table    │      │  - Streaming          │
│  - Feedback table        │      │  - Token counting     │
│  - Interaction events    │      │                       │
│  - Session data          │      │                       │
└──────────────────────────┘      └───────────────────────┘
```

### Technology Stack

**Frontend:**
- **Framework:** Next.js 14.2.15 (React 18.3.1)
- **Language:** TypeScript 5.9.3
- **CSS:** Inline styles (no CSS framework specified)
- **HTTP Client:** Fetch API (built-in)
- **State Management:** React hooks (useState, useRef, useEffect)
- **Supabase Client:** @supabase/supabase-js 2.46.1

**Backend:**
- **Framework:** FastAPI (Python 3.10+)
- **Server:** Uvicorn
- **Language:** Python 3.10+
- **CORS Handling:** fastapi.middleware.cors.CORSMiddleware
- **HTTP Client:** requests library
- **LLM Client:** OpenAI Python SDK (4.63.0)

**Database:**
- **Primary Storage:** Supabase (PostgreSQL-based)
- **Schema Management:** Manual SQL
- **REST API:** Supabase PostgREST

**Infrastructure:**
- **Hosting:** Vercel (serverless)
- **Environment:** Supports local development and production
- **Build System:** Next.js build, Python requirements.txt

**Optional Integrations:**
- **LLM Provider:** OpenAI (gpt-4o-mini recommended)
- **Analytics/Persistence:** Supabase (optional, gracefully degrades)

---

## Design Principles

### 1. **Separation of Concerns**

The application cleanly separates:
- **Frontend (Next.js):** UI rendering, user interaction, client-side state
- **Backend (FastAPI):** Business logic, LLM orchestration, data access
- **Storage (Supabase):** Data persistence, transaction management
- **Configuration:** Environment-driven, externalized from code

### 2. **Progressive Enhancement**

The system is designed to work at multiple capability levels:
- **Minimal:** Rule-based responses, no external services
- **Enhanced:** With Supabase for persistence
- **Full Featured:** With OpenAI LLM integration for generated responses
- **Research Mode:** With comprehensive interaction event logging

Each enhancement is optional and the system degrades gracefully if services are unavailable.

### 3. **Stateless Backend Architecture**

The FastAPI backend is designed to be stateless to support serverless deployment:
- Session history kept in-memory (or queried from Supabase)
- No sticky sessions required
- Each function invocation is independent
- Session data can be reconstructed from database

### 4. **Research-First Design**

The architecture prioritizes research instrumentation:
- Detailed interaction event logging
- Participant tracking and grouping (A/B variants)
- Scenario-based conversation framing
- Standardized feedback rubrics
- LLM-as-Judge evaluation compatibility

### 5. **Streaming-Optimized**

The system is optimized for real-time token streaming:
- Server-Sent Events (SSE) for efficient streaming
- Chunked text output to provide responsive UX
- First-token-time tracking
- Complete reply tracking
- Partial response handling

### 6. **Configuration-Driven**

All major behaviors are controlled via environment variables:
- LLM provider and model selection
- Assistant mode (open vs. strict)
- Streaming behavior
- Supabase integration
- Origin and provider details

### 7. **Best-Effort Persistence**

Data persistence is optional and best-effort:
- System continues to function without Supabase
- Failed persistence attempts log but don't block requests
- Client-side state is authoritative for chat flow
- Server-side logs provide audit trail

---

## System Components

### Component Breakdown

```
VodaCare Support System
├── Frontend Components
│   ├── ChatWindow (main interaction component)
│   ├── MessageBubble (message display)
│   ├── Markdown (rich text rendering)
│   ├── ParticipantForm (enrollment)
│   ├── FeedbackForm (rubric-based feedback)
│   └── ScenarioSelector (scenario selection)
│
├── Backend Modules
│   ├── Agent (SupportAgent - conversation logic)
│   ├── Storage (SupabaseStore - data access)
│   ├── Config (environment & configuration)
│   ├── Models (Pydantic data models)
│   └── Main (FastAPI application setup)
│
├── API Routes
│   ├── /api/chat (synchronous replies)
│   ├── /api/chat-stream (SSE streaming replies)
│   ├── /api/messages (message retrieval/storage)
│   ├── /api/participants (participant management)
│   ├── /api/feedback (feedback submission)
│   ├── /api/interaction (event logging)
│   ├── /api/scenarios (scenario retrieval)
│   └── /api/health (health check)
│
├── Data Models
│   ├── ChatRequest (user message + metadata)
│   ├── ChatResponse (reply + metadata)
│   ├── InteractionEvent (telemetry data)
│   ├── ParticipantInsert (user enrollment)
│   ├── MessageInsert (message persistence)
│   └── FeedbackInsert (feedback submission)
│
└── Testing Framework
    ├── LLM simulation (persona-based)
    ├── Human testing interface
    ├── LAJ (LLM-as-Judge) evaluation
    └── Comparison reporting
```

---

## Frontend Design

### Architecture Overview

The frontend is a Next.js 14 application with a single main component (ChatWindow) managing the complete chat interface. The design emphasizes simplicity while supporting complex interactions.

### Page Structure

```
web/
├── app/
│   ├── layout.tsx (root layout with title/meta)
│   ├── page.tsx (entry point, renders ChatWindow)
│   └── api/
│       ├── interaction/ (telemetry submission)
│       └── feedback/ (feedback submission via backend)
├── components/
│   ├── ChatWindow.tsx (main chat interface - 1000+ lines)
│   ├── MessageBubble.tsx (individual message display)
│   └── Markdown.tsx (markdown rendering for rich replies)
├── lib/
│   ├── api.ts (API client functions)
│   └── telemetry.ts (event logging)
├── public/
│   └── [static assets]
├── package.json
└── tsconfig.json
```

### ChatWindow Component Design

The ChatWindow is the primary user interface component managing:

**State Management:**
```typescript
// Message history
const [messages, setMessages] = useState<Msg[]>([...])

// Session & participant tracking
const [sessionId, setSessionId] = useState<string | undefined>()
const [participantId, setParticipantId] = useState<string | undefined>()
const [participantName, setParticipantName] = useState<string>()
const [participantGroup, setParticipantGroup] = useState<"A" | "B" | "">()

// Conversation state
const [input, setInput] = useState("")
const [busy, setBusy] = useState(false)

// Streaming behavior
const [useStreaming, setUseStreaming] = useState(
  process.env.NEXT_PUBLIC_USE_STREAMING !== "false"
)

// Scenario selection
const [scenarios, setScenarios] = useState<any[]>()
const [selectedScenario, setSelectedScenario] = useState<string>()
const [scenarioContext, setScenarioContext] = useState<string>()

// Feedback collection
const [showFeedback, setShowFeedback] = useState(false)
const [feedbackForm, setFeedbackForm] = useState({
  rating_overall: 0,
  rating_task_success: 0,
  rating_clarity: 0,
  rating_empathy: 0,
  rating_accuracy: 0,
  resolved: "",
  comments_other: ""
})

// Telemetry
const [typingStartAt, setTypingStartAt] = useState<number | null>()
const [lastSendAt, setLastSendAt] = useState<number | null>()
```

**Key Functions:**

1. **Initialization Flow:**
   - Load scenarios from `/api/scenarios`
   - Create session ID if not exists
   - Load previous messages from Supabase if available
   - Initialize participant tracking

2. **Message Sending Flow:**
   - Validate input
   - Create user message locally
   - Record typing duration telemetry
   - Choose streaming or non-streaming path based on config
   - Update message history with assistant reply
   - Log telemetry events

3. **Streaming Flow (if enabled):**
   - Open EventSource to `/api/chat-stream`
   - Receive `init` event with metadata
   - Accumulate `token` events into reply text
   - Append complete message on `done` event
   - Handle connection errors gracefully

4. **Feedback Submission:**
   - Validate rubric ratings
   - Submit to `/api/feedback`
   - Track resolution status
   - Log optional comments
   - Clear form after submission

5. **Telemetry Logging:**
   - Log message send events
   - Track input focus/blur
   - Measure typing duration
   - Record participant interactions
   - Submit batched events to `/api/interaction`

**UI Sections:**

1. **Enrollment Gate (if not started):**
   - Participant name input
   - Group selection (A/B)
   - Start conversation button
   - Optional: Scenario selection dropdown

2. **Scenario Display (if selected):**
   - Scenario title and description
   - Context for the conversation

3. **Chat History:**
   - Scrollable message list
   - User messages (right-aligned, light background)
   - Assistant messages (left-aligned, dark background)
   - Markdown rendering in assistant messages
   - Auto-scroll to latest message

4. **Input Area:**
   - Text input field
   - Send button (disabled while busy)
   - Loading indicator during message processing
   - Optional streaming indicator

5. **Finish Button:**
   - Ends conversation
   - Triggers feedback form
   - Saves messages to Supabase

6. **Feedback Form (modal overlay):**
   - Overall rating (1-5 stars)
   - Task success rating (Likert scale)
   - Clarity rating (Likert scale)
   - Empathy rating (Likert scale)
   - Accuracy rating (Likert scale)
   - Resolution status (Yes/No/Partial)
   - Comments text area
   - Submit button

### Design Decisions

**Single Component Approach:**
- ChatWindow is a large monolithic component (~1000+ lines)
- Rationale: Tight coupling of state management and UI, easier for research instrumentation
- Trade-off: Less reusable but more cohesive for FYP purposes

**Local-First State:**
- Message history kept in React state initially
- Persisted to Supabase asynchronously
- Rationale: Fast UI responsiveness, eventual consistency acceptable
- Fallback: Can recover from Supabase if needed

**Streaming Choice:**
- Controlled by `NEXT_PUBLIC_USE_STREAMING` environment variable
- Frontend makes the choice, not runtime negotiation
- Rationale: Simplicity, environment-based feature flagging

**Scenario Integration:**
- Optional scenario selection before chat
- Scenarios fetched from backend `/api/scenarios`
- Context displayed during conversation
- Rationale: Research requirement for scenario-guided testing

### Responsive Design Considerations

- Mobile-first approach (no explicit viewport constraints in current design)
- Touch-friendly input and button sizes
- Scrollable message area for long conversations
- Modal feedback form for explicit completion
- Supports both narrow (mobile) and wide (desktop) layouts

---

## Backend Design

### Architecture Overview

The backend is a FastAPI application designed for serverless deployment on Vercel. It handles all business logic, LLM orchestration, and data access.

### Module Structure

```
server/
├── app/
│   ├── __init__.py
│   ├── main.py (FastAPI application & route handlers)
│   ├── agent.py (SupportAgent - conversation logic)
│   ├── storage.py (SupabaseStore - data access layer)
│   ├── models.py (Pydantic data models)
│   ├── config.py (environment configuration)
│   └── ...
├── api/
│   ├── scenarios.py (scenario management routes)
│   ├── interaction.py (interaction event handling)
│   └── [other route-specific modules]
├── requirements.txt (Python dependencies)
└── venv/ (virtual environment)
```

### FastAPI Application Setup

**Application Initialization:**
```python
app = FastAPI(
    title="VodaCare Support API",
    version="0.1.0"
)

# Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router registration
app.include_router(
    scenarios_router.router,
    prefix="/api",
    tags=["scenarios"]
)
```

**Global Service Initialization:**
```python
# Main business logic agent
agent = SupportAgent()

# Data persistence layer
store = SupabaseStore()
```

### SupportAgent Design

The `SupportAgent` class encapsulates all conversation logic:

**Initialization:**
```python
class SupportAgent:
    def __init__(self):
        self.provider = get_provider_name()  # e.g., "VodaCare"
        self.mode = get_assistant_mode()     # "open" or "strict"

        # In-memory session storage
        self.sessions: Dict[str, List[Tuple[str, str]]] = {}

        # Optional LLM client
        self._llm_client = None  # OpenAI client if configured
        self._llm_model = get_openai_model()  # e.g., "gpt-4o-mini"

        # Knowledge base for rule-based responses
        self.knowledge = {
            "plans": {...},
            "balance": {...},
            "billing": {...},
            "roaming": {...},
            "network": {...},
            "support": {...},
            "device": {...}
        }

        # Quick-reply mapping
        self.quick_map = {...}
```

**Key Methods:**

1. **`chat(message, session_id, participant_group) -> ChatResponse`**
   - Main synchronous chat method
   - Detects intent/topic from message
   - Generates rule-based or LLM-powered reply
   - Returns structured response with metadata

2. **`_ensure_session(session_id) -> str`**
   - Creates or retrieves session
   - Returns guaranteed non-None session ID
   - Manages in-memory history

3. **`_detect_topic(message) -> str`**
   - Keyword-based intent detection
   - Checks message against knowledge base keywords
   - Returns topic identifier or "unknown"

4. **`_get_reply(topic, message, session_id) -> str`**
   - Selects rule-based or LLM-powered reply
   - Rule-based: Returns prewritten response from knowledge base
   - LLM-powered: Streams response from OpenAI via chat completion API

5. **`_system_prompt(participant_group) -> str`**
   - Generates system prompt for LLM
   - Can vary by variant/group if needed
   - Establishes assistant personality and constraints

**Knowledge Base Structure:**

Each topic has:
```python
topic_name: {
    "desc": "Human-readable description",
    "reply": "Default rule-based response",
    "suggestions": ["Quick reply option 1", "Quick reply option 2", ...],
    "keywords": ["keyword1", "keyword2", ...]  # For intent detection
}
```

**LLM Integration:**

The agent can optionally use OpenAI's API:
```python
# Lazy initialization
if api_key := get_openai_api_key():
    from openai import OpenAI
    self._llm_client = OpenAI(
        api_key=api_key,
        base_url=get_openai_base_url()  # Optional proxy/Azure
    )
```

When LLM is available, responses are streamed:
```python
stream = self._llm_client.chat.completions.create(
    model=self._llm_model,
    messages=[...],
    temperature=0.5 if self.mode == "open" else 0.3,
    max_tokens=220,
    stream=True
)

for chunk in stream:
    token = chunk.choices[0].delta.content
    yield token
```

### SupabaseStore Design

The `SupabaseStore` class provides a simple data access layer:

**Initialization:**
```python
class SupabaseStore:
    def __init__(self):
        self.url = get_supabase_url()        # Supabase project URL
        self.key = get_supabase_service_key() # Service role key

    def is_configured(self) -> bool:
        return bool(self.url and self.key)
```

**Core Methods:**

1. **`insert_rows(table, rows, upsert=False, on_conflict=None)`**
   - Bulk insert via Supabase REST API
   - Optional upsert with conflict resolution
   - Returns (count_inserted, status_code)
   - Gracefully handles conflicts (409) as no-op

2. **`update_by_pk(table, pk_col, pk_value, fields)`**
   - Single-row PATCH via PostgREST
   - Updates specific fields only
   - Returns (count_updated, status_code)

3. **`select_rows(table, filters, select=None, order=None, limit=None)`**
   - Query rows with PostgREST filters
   - Optional column selection
   - Optional ordering and limiting
   - Supports pagination

**HTTP Headers & Authentication:**
```python
def _headers(self, upsert=False) -> Dict[str, str]:
    h = {
        "apikey": self.key or "",
        "Authorization": f"Bearer {self.key}",
        "Content-Type": "application/json",
    }
    if upsert:
        h["Prefer"] = "resolution=merge-duplicates,return=minimal"
    return h
```

**Error Handling:**
- Logs detailed error context on failures
- Returns (0, status_code) on error
- 409 Conflict treated as no-op (not an error)
- Best-effort: doesn't block request processing

### Configuration Management

The `config.py` module handles all environment configuration:

```python
def get_provider_name() -> str:
    return os.getenv("PROVIDER_NAME", "VodaCare")

def get_openai_api_key() -> Optional[str]:
    return os.getenv("OPENAI_API_KEY")

def get_openai_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def get_openai_base_url() -> Optional[str]:
    return os.getenv("OPENAI_BASE_URL")

def get_assistant_mode() -> str:
    # "open" (default) or "strict"
    return os.getenv("ASSISTANT_MODE", "open")

def get_supabase_url() -> Optional[str]:
    return os.getenv("SUPABASE_URL")

def get_supabase_service_key() -> Optional[str]:
    return os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def get_allowed_origins() -> List[str]:
    origins = os.getenv("ALLOWED_ORIGINS", "")
    return [o.strip() for o in origins.split(",") if o.strip()]
```

All configuration is **environment variable driven**, enabling:
- Simple deployment across environments
- No code changes for configuration
- Security (secrets never in code)
- Runtime behavior changes without redeployment

---

## Data Model & Storage

### Data Model Overview

The system uses several Pydantic models for request/response validation:

**Request Models:**
```python
class ChatRequest(BaseModel):
    message: str                          # User's message
    session_id: Optional[str] = None      # Session identifier
    participant_group: Optional[str] = None  # "A" or "B"
    participant_id: Optional[str] = None
    page_url: Optional[str] = None
```

**Response Models:**
```python
class ChatResponse(BaseModel):
    reply: str                            # Assistant's response
    suggestions: List[str]                # Quick reply suggestions (now empty)
    topic: str                            # Detected topic/intent
    escalate: bool = False                # Escalation flag
    session_id: str                       # Session identifier (guaranteed)
```

**Event Logging:**
```python
class InteractionEvent(BaseModel):
    session_id: str                       # Required: session reference
    participant_id: Optional[str]
    participant_group: Optional[str]      # "A" or "B"
    event: str                            # Event type: "click", "typing", "message_send"
    component: Optional[str]              # UI component name
    label: Optional[str]                  # Event label
    value: Optional[str]                  # Event value
    duration_ms: Optional[int]            # Duration in milliseconds
    client_ts: Optional[Union[str, int]]  # Timestamp (ISO or epoch)
    page_url: Optional[str]
    user_agent: Optional[str]
    meta: Optional[dict]                  # Arbitrary metadata
```

**Participant Management:**
```python
class ParticipantInsert(BaseModel):
    participant_id: str
    name: Optional[str]
    group: Optional[str]                  # "A" or "B"
    session_id: Optional[str]
    scenario_id: Optional[str]            # Scenario being tested
```

**Message Persistence:**
```python
class MessageInsert(BaseModel):
    session_id: str
    role: str                             # "user" or "assistant"
    content: str
    participant_id: Optional[str]
    participant_name: Optional[str]
    participant_group: Optional[str]
```

**Feedback Collection:**
```python
class FeedbackInsert(BaseModel):
    session_id: Optional[str]
    participant_id: Optional[str]
    participant_group: Optional[str]
    scenario_id: Optional[str]

    # Rubric-based ratings (1-5 scale)
    rating_overall: Optional[int]
    rating_task_success: Optional[int]    # 50% weight in LAJ rubric
    rating_clarity: Optional[int]          # 20% weight
    rating_empathy: Optional[int]          # 20% weight
    rating_accuracy: Optional[int]         # 10% weight (policy compliance)

    resolved: Optional[bool]              # Yes/No/Partial
    comments_other: Optional[str]
    user_agent: Optional[str]
    page_url: Optional[str]
```

### Database Schema

The Supabase backend uses the following tables:

**`participants` table:**
```sql
CREATE TABLE participants (
    participant_id TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    name TEXT,
    group TEXT CHECK (group IN ('A', 'B')),
    session_id TEXT,
    scenario_id TEXT
);
```

**`messages` table:**
```sql
CREATE TABLE messages (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    session_id TEXT,
    role TEXT CHECK (role IN ('user', 'assistant')),
    content TEXT,
    participant_id TEXT,
    participant_name TEXT,
    participant_group TEXT CHECK (participant_group IN ('A', 'B'))
);

-- Indexes for performance
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

**`support_feedback` table:**
```sql
CREATE TABLE support_feedback (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    session_id TEXT,
    participant_id TEXT,
    participant_group TEXT CHECK (participant_group IN ('A', 'B')),
    scenario_id TEXT,
    rating_overall INTEGER,
    rating_task_success INTEGER CHECK (rating_task_success >= 1 AND rating_task_success <= 5),
    rating_clarity INTEGER CHECK (rating_clarity >= 1 AND rating_clarity <= 5),
    rating_empathy INTEGER CHECK (rating_empathy >= 1 AND rating_empathy <= 5),
    rating_accuracy INTEGER CHECK (rating_accuracy >= 1 AND rating_accuracy <= 5),
    resolved BOOLEAN,
    comments_other TEXT,
    user_agent TEXT,
    page_url TEXT
);

-- Indexes for research queries
CREATE INDEX idx_feedback_participant_group ON support_feedback(participant_group);
CREATE INDEX idx_feedback_scenario_id ON support_feedback(scenario_id);
```

**`interaction_events` table:**
```sql
CREATE TABLE interaction_events (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    session_id TEXT,
    participant_id TEXT,
    participant_group TEXT CHECK (participant_group IN ('A', 'B')),
    event TEXT,
    component TEXT,
    label TEXT,
    value TEXT,
    duration_ms INTEGER,
    client_ts TIMESTAMPTZ,
    page_url TEXT,
    user_agent TEXT,
    meta JSONB
);

-- Indexes for telemetry analysis
CREATE INDEX idx_interaction_events_session ON interaction_events(session_id);
CREATE INDEX idx_interaction_events_event ON interaction_events(event);
CREATE INDEX idx_interaction_events_participant_group ON interaction_events(participant_group);
```

**`scenarios` table:**
```sql
CREATE TABLE scenarios (
    id TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    context TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Interactions table (Deprecated)

```sql
CREATE TABLE interactions (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    "group" TEXT CHECK ("group" IN ('A', 'B')),
    input TEXT,
    output TEXT
);
```

This table is deprecated in favor of `interaction_events` for more granular telemetry.

### Row-Level Security (RLS)

For local development with anonymous access:
```sql
-- Allow anonymous users to insert
CREATE POLICY "allow anon inserts messages"
ON messages FOR INSERT TO anon USING (true) WITH CHECK (true);

CREATE POLICY "allow anon inserts participants"
ON participants FOR INSERT TO anon USING (true) WITH CHECK (true);

CREATE POLICY "allow anon inserts interactions"
ON interactions FOR INSERT TO anon USING (true) WITH CHECK (true);

CREATE POLICY "allow anon inserts feedback"
ON support_feedback FOR INSERT TO anon USING (true) WITH CHECK (true);

CREATE POLICY "allow anon inserts events"
ON interaction_events FOR INSERT TO anon USING (true) WITH CHECK (true);
```

**Production RLS Policies:**
- Restrict write access to service role only
- Allow selective read access for analytics
- Implement participant data isolation if needed

### Storage Characteristics

**Persistence Model:**
- **Write pattern:** Bulk inserts, append-only logs
- **Read pattern:** Historical queries for analysis
- **Consistency:** Eventually consistent (async logging)
- **Guarantees:** Best-effort persistence, failures logged
- **Scalability:** Supabase handles horizontal scaling

**Data Lifecycle:**
- **Messages:** Persisted immediately when session ends
- **Events:** Asynchronously logged, may be lost if backend crashes
- **Feedback:** Synchronously persisted, retried on failure
- **Participants:** Persisted on enrollment and updates
- **Retention:** No automatic expiration (manual cleanup if needed)

---

## API Design

### API Principles

1. **REST Convention:** Standard HTTP methods and status codes
2. **JSON Format:** All request/response bodies are JSON
3. **Session-Aware:** Most endpoints require or track `session_id`
4. **Best-Effort:** Failures don't block primary conversation flow
5. **Type-Safe:** Pydantic models ensure request/response validation
6. **Idempotent:** Write operations should be safe to retry

### Endpoint Specifications

#### `POST /api/chat` - Synchronous Chat

**Purpose:** Send a message and receive an immediate response

**Request:**
```json
{
  "message": "How do I check my data balance?",
  "session_id": "abc123",
  "participant_group": "A",
  "participant_id": "p_001",
  "page_url": "https://example.com/chat"
}
```

**Response:**
```json
{
  "reply": "Check remaining data and minutes in the app or text BALANCE to 12345.",
  "suggestions": [],
  "topic": "balance",
  "escalate": false,
  "session_id": "abc123"
}
```

**HTTP Status:**
- `200 OK`: Successful response
- `400 Bad Request`: Invalid request body
- `500 Internal Server Error`: Server error (reply may be error message)

**Implementation Details:**
- Non-streaming, synchronous
- Suitable for quick API testing
- Used as fallback if streaming unavailable

---

#### `POST /api/chat-stream` - Streaming Chat (SSE)

**Purpose:** Send a message and receive streamed response tokens

**Request:**
```json
{
  "message": "I want to upgrade my plan",
  "session_id": "abc123",
  "participant_group": "B",
  "participant_id": "p_001"
}
```

**Response Format:** Server-Sent Events (text/event-stream)

**Event Stream:**
```
event: init
data: {"session_id": "abc123", "suggestions": [], "topic": "plans", "escalate": false, "engine": "openai"}

event: token
data: We

event: token
data:  offer

event: token
data: SIM‑only

event: token
data: ...

event: done
data: {"reply": "We offer SIM-only and device plans..."}
```

**Event Types:**

1. **`init` Event (first):**
   - Sent immediately when request received
   - Contains metadata for UI initialization
   - Includes: session_id, suggestions, topic, escalate flag, engine

2. **`token` Events (streaming):**
   - Partial text tokens from LLM
   - Each event contains partial text (typically ~40 chars)
   - Respects word boundaries to avoid mid-word splits
   - Streamed in real-time

3. **`done` Event (last):**
   - Final event with complete reply
   - Contains: reply (full text)
   - Signals end of response

**Telemetry Events (Server-Side):**
- `reply_init`: When response streaming starts
- `first_token`: When first token received from LLM (with TTFT_ms)
- `reply_done`: When response complete (with duration_ms)

**HTTP Status:**
- `200 OK`: Successful SSE stream
- `400 Bad Request`: Invalid request
- `500 Internal Server Error`: Server error (sent as token event)

**Error Handling:**
- If LLM unavailable: Server sends error message as tokens
- If LLM fails: Gracefully degrades to error text
- Connection drops: Frontend reconnects or falls back to polling

**Implementation Details:**
```python
@app.post("/api/chat-stream")
async def chat_stream(req: ChatRequest, request: Request):
    async def event_gen() -> AsyncGenerator[bytes, None]:
        # Ensure session
        sid = agent._ensure_session(req.session_id)
        agent.sessions[sid].append(("user", req.message))

        # Determine topic & escalation
        topic = agent._detect_topic(req.message)
        escalate = topic == "support" or "escalate" in req.message.lower()

        # Send init event
        init_payload = json.dumps({
            "session_id": sid,
            "suggestions": [],
            "topic": topic,
            "escalate": escalate,
            "engine": "openai" if agent._llm_client else "error"
        })
        yield sse("init", init_payload)

        # Stream LLM response
        full_reply = ""
        if agent._llm_client:
            stream = agent._llm_client.chat.completions.create(...)
            for chunk in stream:
                token = chunk.choices[0].delta.content
                if token:
                    full_reply += token
                    yield sse("token", token)
        else:
            # Error text if no LLM
            error_reply = "Service unavailable..."
            for part in _chunk_text_for_stream(error_reply):
                full_reply += part
                yield sse("token", part)

        # Save and send done
        agent.sessions[sid].append(("assistant", full_reply))
        yield sse("done", json.dumps({"reply": full_reply}))

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

---

#### `GET /api/health` - Health Check

**Purpose:** Verify API availability and configuration

**Response:**
```json
{
  "status": "ok",
  "provider": "VodaCare",
  "storage_configured": true
}
```

**HTTP Status:**
- `200 OK`: Service is healthy

**Use Cases:**
- Liveness probes (Kubernetes, load balancers)
- CI/CD pipeline health checks
- Frontend initialization validation

---

#### `POST /api/messages` - Store Message

**Purpose:** Persist a message to Supabase

**Request:**
```json
{
  "session_id": "abc123",
  "role": "user",
  "content": "How do I roam internationally?",
  "participant_id": "p_001",
  "participant_name": "Alice",
  "participant_group": "A"
}
```

**Response:**
```json
{
  "ok": true,
  "stored": 1
}
```

**HTTP Status:**
- `200 OK`: Message stored successfully
- `202 Accepted`: Request accepted but not stored (Supabase unavailable)
- `400 Bad Request`: Invalid request body
- `500 Internal Server Error`: Critical error

**Idempotency:** Safe to call multiple times (idempotent in behavior)

---

#### `GET /api/messages?session_id=abc123` - Retrieve Messages

**Purpose:** Fetch all messages for a session

**Response:**
```json
{
  "messages": [
    {
      "session_id": "abc123",
      "role": "user",
      "content": "How do I check my balance?",
      "participant_id": "p_001",
      "participant_name": "Alice",
      "participant_group": "A",
      "created_at": "2024-02-18T10:30:00Z"
    },
    {
      "session_id": "abc123",
      "role": "assistant",
      "content": "Check your balance by...",
      "created_at": "2024-02-18T10:30:05Z"
    }
  ]
}
```

**HTTP Status:**
- `200 OK`: Messages retrieved
- `500 Internal Server Error`: Query failed

**Implementation Details:**
- Orders by created_at ascending
- Limits to 200 most recent messages
- Falls back to unordered if timestamp column missing
- Best-effort: returns empty list on failure

---

#### `POST /api/participants` - Create/Update Participant

**Purpose:** Enroll a participant or update their session

**Request (Enrollment):**
```json
{
  "participant_id": "p_001",
  "name": "Alice Smith",
  "group": "A",
  "session_id": "abc123"
}
```

**Request (Session Update):**
```json
{
  "participant_id": "p_001",
  "session_id": "def456"
}
```

**Response:**
```json
{
  "ok": true,
  "stored": 1
}
```

**HTTP Status:**
- `200 OK`: Participant created/updated
- `202 Accepted`: Request accepted but not persisted
- `500 Internal Server Error`: Error

**Implementation Details:**
- Upserts by participant_id
- If only participant_id + session_id provided, updates session only
- Otherwise, creates or replaces full record

---

#### `POST /api/feedback` - Submit Feedback

**Purpose:** Collect rubric-based feedback on the conversation

**Request:**
```json
{
  "session_id": "abc123",
  "participant_id": "p_001",
  "participant_group": "A",
  "scenario_id": "roaming_activation",
  "rating_overall": 4,
  "rating_task_success": 4,
  "rating_clarity": 5,
  "rating_empathy": 4,
  "rating_accuracy": 3,
  "resolved": true,
  "comments_other": "The assistant was helpful but could have offered more plan options.",
  "user_agent": "Mozilla/5.0...",
  "page_url": "https://example.com/chat"
}
```

**Response:**
```json
{
  "ok": true,
  "stored": true
}
```

**HTTP Status:**
- `200 OK`: Feedback stored
- `202 Accepted`: Request accepted but not stored
- `400 Bad Request`: Invalid request
- `500 Internal Server Error`: Error with diagnostics message

**Failure Messages:**
```json
{
  "ok": false,
  "error": "supabase_not_configured"
}
```

**Implementation Details:**
- Logs detailed configuration diagnostics on failure
- Retries on transient failures
- Includes user-agent from request headers if not provided
- Critical endpoint for research (has extensive logging)

---

#### `POST /api/interaction` - Log Interaction Events

**Purpose:** Submit detailed telemetry about user interactions

**Request (Single Event):**
```json
{
  "session_id": "abc123",
  "event": "message_send",
  "component": "chat_input",
  "label": "user_message_sent",
  "duration_ms": 2500,
  "client_ts": "2024-02-18T10:30:00Z",
  "participant_id": "p_001",
  "participant_group": "A"
}
```

**Request (Multiple Events):**
```json
[
  {
    "session_id": "abc123",
    "event": "input_focus",
    "component": "chat_input",
    "client_ts": 1708169400000
  },
  {
    "session_id": "abc123",
    "event": "message_send",
    "component": "chat_input",
    "duration_ms": 2500
  }
]
```

**Request (Batch Format):**
```json
{
  "events": [...]
}
```

**Response:**
```json
{
  "ok": true,
  "stored": 2
}
```

**HTTP Status:**
- `200 OK`: Events stored
- `202 Accepted`: Request accepted, events skipped (no Supabase)
- `400 Bad Request`: Invalid JSON
- `500 Internal Server Error`: Error

**Event Types Logged:**
- `input_focus`: User focused on input field
- `input_blur`: User left input field
- `typing`: User typing (with duration)
- `message_send`: User sent message (with duration_ms)
- `suggestion_click`: User clicked suggestion
- `reply_init`: Server initiated response
- `first_token`: First token received from LLM
- `reply_done`: Response complete
- Custom events: Any other events from client

**Implementation Details:**
- Accepts single object, array, or {events: [...]}
- Validates and filters invalid events
- Logs verbose rows to `interaction_events` table
- Treats missing session_id as validation error (skips)
- Ignores deprecated compact interaction shape

---

#### `GET /api/scenarios` - List Available Scenarios

**Purpose:** Fetch list of scenarios for scenario-guided testing

**Response:**
```json
{
  "scenarios": [
    {
      "id": "esim_setup",
      "title": "eSIM Setup",
      "description": "Help customer set up eSIM on their device",
      "context": "You need to set up eSIM on your new phone but aren't sure how to start the process."
    },
    {
      "id": "roaming_activation",
      "title": "Roaming Activation",
      "description": "Enable international roaming for travel",
      "context": "You're traveling to France next week and need to enable roaming on your plan."
    },
    ...
  ]
}
```

**HTTP Status:**
- `200 OK`: Scenarios retrieved
- `500 Internal Server Error`: Query failed

**Implementation Details:**
- Scenarios stored in database
- Frontend displays to user for selection
- Context provided to guide conversation
- Optional: Used in feedback submission for research correlation

---

### API Design Patterns

**Error Response Format:**
```json
{
  "ok": false,
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {...}
}
```

**Status Code Conventions:**
- `200 OK`: Successful and persisted
- `202 Accepted`: Successful but not persisted (retry safe)
- `400 Bad Request`: Client error (bad request body)
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error (retryable)

**Rate Limiting:** Not currently implemented (can add per-IP if needed)

**CORS Headers:** Controlled via environment variable `ALLOWED_ORIGINS`

---

## LLM Integration & Streaming

### LLM Architecture

**Optional Integration:**
- LLM is completely optional
- System functions in rule-based mode without OpenAI API key
- When available, enhances responses with generative completions

**Lazy Initialization:**
```python
api_key = get_openai_api_key()
if api_key:
    try:
        from openai import OpenAI
        self._llm_client = OpenAI(
            api_key=api_key,
            base_url=get_openai_base_url()  # Optional proxy
        )
    except Exception as e:
        logger.exception("Failed to init OpenAI client")
        self._llm_client = None  # Graceful degradation
```

**Model Selection:**
- Default: `gpt-4o-mini` (fast, low-cost)
- Configurable: `OPENAI_MODEL` environment variable
- Can use Azure OpenAI: `OPENAI_BASE_URL` for proxy

### Streaming Implementation

**Server-Sent Events (SSE):**
- Standard HTTP streaming protocol
- Efficient for real-time text updates
- Supported by modern browsers
- Easier than WebSockets for serverless

**Stream Lifecycle:**

1. **Request Phase:**
   - Client POST to `/api/chat-stream`
   - Server validates request
   - Creates session if needed

2. **Initialization Phase:**
   - Server sends `init` event with metadata
   - Includes: session_id, topic, escalate, engine
   - Frontend initializes UI state

3. **Token Streaming Phase:**
   - LLM generates response token-by-token
   - Each token sent as separate `token` event
   - Text chunked at word boundaries (~40 chars)
   - Server measures time-to-first-token (TTFT)

4. **Completion Phase:**
   - All tokens consumed from LLM
   - Complete reply sent in `done` event
   - Server logs completion telemetry
   - Frontend appends final message to history

**Token Chunking Strategy:**
```python
def _chunk_text_for_stream(text: str):
    """Chunk text into ~40 character chunks respecting word boundaries."""
    buf = []
    count = 0
    for word in text.split(" "):
        if count + len(word) + (1 if buf else 0) > 40:
            yield (" ".join(buf)) + " "
            buf = [word]
            count = len(word)
        else:
            buf.append(word)
            count += len(word) + (1 if count > 0 else 0)
    if buf:
        yield " ".join(buf)
```

**Client-Side Handling:**
```typescript
// Frontend receives and processes SSE events
const eventSource = new EventSource('/api/chat-stream');

eventSource.addEventListener('init', (event) => {
  const data = JSON.parse(event.data);
  setSessionId(data.session_id);
  setTopic(data.topic);
  setEscalate(data.escalate);
});

eventSource.addEventListener('token', (event) => {
  setReply(prev => prev + event.data);
});

eventSource.addEventListener('done', (event) => {
  const data = JSON.parse(event.data);
  // Complete message received
  addMessageToHistory('assistant', data.reply);
  eventSource.close();
});
```

### System Prompt Design

**Dynamic System Prompt:**
```python
def _system_prompt(self, participant_group: Optional[str]) -> str:
    """Generate system prompt for LLM."""
    prompt = f"""You are a helpful customer support assistant for {self.provider}.
Your role is to assist customers with questions about:
- Plans and upgrades
- Billing and payments
- Data and usage
- Roaming and international services
- Network coverage and technical issues
- Device management
- Escalation to human support

You are polite, empathetic, and knowledgeable. Provide accurate information without speculation.
If unsure, offer to escalate to a human agent.

Assistant Mode: {self.mode}
"""
    if self.mode == "strict":
        prompt += "Restrict responses to telecom/support topics only."
    return prompt
```

**Mode Variations:**
- `open` (default): Allow general conversation
- `strict`: Restrict to telecom topics only

**Variant-Specific Prompts:**
- Can customize per participant_group (A/B testing)
- Currently same for both groups
- Extensible for future prompt variations

### Performance Characteristics

**Latency Metrics:**
- **Time-to-First-Token (TTFT):** ~500-2000ms (measured server-side)
- **Token Generation Rate:** ~50-100 tokens/second
- **Total Response Time:** 2-5 seconds for typical response

**Streaming Benefits:**
- Perceived latency: Tokens appear immediately (low TTFT)
- Better UX than waiting for full response
- Server load: Reduced memory (streaming vs. buffering)
- Client load: Incremental rendering (efficient)

### Cost Optimization

**Model Selection:**
- `gpt-4o-mini`: ~70% cheaper than `gpt-4`
- Sufficient quality for customer support domain
- Fast enough for real-time streaming

**Token Budgeting:**
- System prompt: ~150 tokens
- Chat history: Last 3 turns (~500 tokens max)
- User message: ~50 tokens (average)
- Max completion: 220 tokens
- **Total per request:** ~900 tokens (~$0.0003 at mini pricing)

**Cost Controls:**
- Optional: Disable LLM to eliminate costs
- Optional: Cache frequently asked topics (rule-based)
- Can implement request quota per session

---

## Testing Framework

### Human-LLM Testing Alignment

The system is designed to enable direct comparison between:
1. **LLM-Simulated Conversations:** Automated interactions with 20 personas × 5 scenarios
2. **Human Conversations:** Real user testing sessions
3. **Evaluation Methods:** Consistent rubric-based evaluation for both

### Scenario Design

**5 Core Scenarios:**
1. **eSIM Setup** - Technical task, clear success criteria
2. **Roaming Activation** - Feature enablement, requires navigation
3. **Billing Dispute** - Problem resolution, emotional component
4. **Plan Upgrade** - Purchase intent, consideration process
5. **Network Issue** - Troubleshooting, technical depth

**Scenario Properties:**
```python
{
    "id": "scenario_id",
    "title": "Scenario Title",
    "description": "Brief description of scenario",
    "context": "Detailed context for test participant",
    "success_criteria": ["criterion 1", "criterion 2", ...],
    "expected_topics": ["topic1", "topic2", ...],
    "difficulty": "easy|medium|hard"
}
```

### Evaluation Rubric

**Unified Rubric for Human & LLM:**

| Dimension | Weight | Scale | Definition |
|-----------|--------|-------|------------|
| **Task Success** | 50% | 1-5 | Did assistant help accomplish the goal? |
| **Clarity** | 20% | 1-5 | How clear were the responses? |
| **Empathy** | 20% | 1-5 | How well did assistant acknowledge situation? |
| **Accuracy** | 10% | 1-5 | Information accurate without speculation? |

**Scale Definitions:**
- **1:** Poor/Not at all
- **2:** Somewhat/Partially
- **3:** Neutral/Adequate
- **4:** Good/Well
- **5:** Excellent/Very well

**Overall Score Calculation:**
```
Overall = (Task Success × 0.5) + (Clarity × 0.2) + (Empathy × 0.2) + (Accuracy × 0.1)
Range: 1.0 - 5.0
```

### LLM-as-Judge Evaluation

**Purpose:** Automated evaluation of human transcripts using LLM

**Process:**
1. Load human transcript (message history)
2. Ask LLM to evaluate against rubric
3. Extract ratings for each dimension
4. Compare human self-ratings vs. LAJ ratings
5. Generate comparison report

**LAJ Prompt Template:**
```
You are evaluating a customer support conversation.
Evaluate the ASSISTANT's responses against the following criteria:

1. Task Success (50% weight): Did assistant help accomplish the customer's goal?
2. Clarity (20% weight): How clear were the responses?
3. Empathy (20% weight): How well did assistant acknowledge the situation?
4. Accuracy (10% weight): Were responses accurate without speculation?

For each criterion, rate 1-5 and explain.

Conversation:
[transcript here]

Respond in JSON:
{
    "task_success": 4,
    "clarity": 5,
    "empathy": 3,
    "accuracy": 4,
    "reasoning": {...}
}
```

### Human Testing Flow

**Pre-Test:**
1. Participant enrolls (name, group A/B)
2. Optional: Select scenario from list
3. Scenario context displayed (if selected)

**During Test:**
1. Conduct conversation naturally
2. Attempt to accomplish scenario goal
3. Chat with assistant (streaming responses)
4. System logs all interactions

**Post-Test:**
1. Click "Finish" to end conversation
2. Complete feedback form with rubric ratings
3. Select resolution status (Yes/No/Partial)
4. Optional: Add comments
5. Submit feedback
6. System persists all data

### Comparison Report

**Report Sections:**

1. **Summary Statistics:**
   - Total conversations (LLM vs. human)
   - Average ratings by dimension
   - Variant breakdown (A vs. B)

2. **Dimension Analysis:**
   - Task Success performance
   - Clarity comparison
   - Empathy metrics
   - Accuracy scores

3. **Variant Comparison:**
   - A/B performance delta
   - Statistical significance (if applicable)
   - Human preference breakdown

4. **Self-Rating vs. LAJ:**
   - Correlation analysis
   - Bias detection
   - Rating discrepancy patterns

5. **Scenario Deep-Dive:**
   - Per-scenario performance
   - Scenario difficulty impact
   - Success patterns by scenario

6. **Methodology Notes:**
   - Sample sizes
   - Collection dates
   - Known limitations

---

## Deployment Architecture

### Vercel Serverless Deployment

**Deployment Target:** Vercel (Next.js + Python Serverless)

**Build Configuration:**

```json
{
  "buildCommand": "cd web && npm install && npm run build",
  "outputDirectory": "web/.next",
  "framework": "nextjs",
  "functions": {
    "python": {
      "memory": 1024,
      "maxDuration": 60
    }
  },
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/server/api/$1"
    }
  ]
}
```

**File Structure on Vercel:**

```
Repository Root
├── web/                  → Next.js app (UI)
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── public/
│   ├── package.json
│   └── .next/           → Built output
├── server/              → Python Serverless Functions
│   ├── api/
│   │   ├── scenarios.py
│   │   ├── chat.py
│   │   └── ...
│   ├── app/
│   │   ├── main.py      → FastAPI app
│   │   ├── agent.py     → Logic
│   │   ├── models.py    → Data models
│   │   └── ...
│   └── requirements.txt  → Python deps
├── vercel.json          → Deployment config
├── .env                 → Local dev config (gitignored)
└── README.md
```

### Local Development Setup

**Prerequisites:**
- Node.js 18+
- Python 3.10+
- Vercel CLI (optional)

**Frontend Development:**

```bash
# From web/ directory
npm install
npm run dev
# Runs on http://localhost:3000
# Proxies /api/* to http://localhost:8000 during dev
```

**Backend Development:**

```bash
# From server/ directory
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# Runs on http://localhost:8000
# FastAPI docs: http://localhost:8000/docs
```

**Environment Variables:**

```bash
# Root .env (used by both apps in local dev)
PROVIDER_NAME=VodaCare
OPENAI_API_KEY=sk-xxx...
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=  # Optional proxy
ASSISTANT_MODE=open
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxx...
NEXT_PUBLIC_USE_STREAMING=true
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx...
ALLOWED_ORIGINS=http://localhost:3000,https://example.com
```

**For Vercel:**
- Set env vars in Vercel dashboard (not in code)
- Do NOT set `NEXT_PUBLIC_API_BASE_URL` (uses relative `/api` paths)
- Frontend automatically uses `/api/*` which routes to Python functions

### Production Considerations

**Scaling:**
- Vercel auto-scales based on load
- Python functions scale independently
- Supabase handles database scaling

**Performance Optimization:**
- CDN caching for static assets (Next.js)
- Connection pooling for Supabase (built-in)
- Redis caching optional (not currently implemented)

**Monitoring:**
- Vercel provides analytics dashboard
- CloudWatch logs for Python functions
- Supabase logs via web UI
- Client-side error tracking (optional)

**Backup & Recovery:**
- Supabase automated backups (daily)
- Database point-in-time recovery available
- Vercel function versioning and rollback

---

## Configuration & Environment Management

### Environment Variables

**Categorized by Purpose:**

**Application Identity:**
- `PROVIDER_NAME`: Provider name (default: "VodaCare")

**LLM Configuration:**
- `OPENAI_API_KEY`: OpenAI API key (required for LLM mode)
- `OPENAI_MODEL`: Model name (default: "gpt-4o-mini")
- `OPENAI_BASE_URL`: Optional proxy/Azure endpoint

**Assistant Behavior:**
- `ASSISTANT_MODE`: "open" (default) or "strict"
  - `open`: General chat allowed
  - `strict`: Only telecom topics

**Streaming:**
- `NEXT_PUBLIC_USE_STREAMING`: "true" (default) or "false"
  - Frontend feature flag for SSE
  - `NEXT_PUBLIC_*` variables are exposed to browser

**Supabase Integration:**
- Server-side (API):
  - `SUPABASE_URL`: Supabase project URL
  - `SUPABASE_SERVICE_ROLE_KEY`: Service role API key
- Client-side (Frontend):
  - `NEXT_PUBLIC_SUPABASE_URL`: Supabase URL (exposed to browser)
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Anon key (exposed to browser)

**CORS:**
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins
  - Example: "http://localhost:3000,https://example.com"
  - Empty: No CORS restrictions
  - Set carefully in production

**Optional Advanced:**
- `LOG_LEVEL`: Logging level (not currently implemented)
- `DATABASE_URL`: Alternative to Supabase (not currently used)

### Configuration Loading

**Backend (Python):**
```python
from dotenv import load_dotenv
import os

# Automatically loads .env or .env.local
load_dotenv()

def get_openai_api_key() -> Optional[str]:
    return os.getenv("OPENAI_API_KEY")
```

**Frontend (Next.js):**
```typescript
// NEXT_PUBLIC_* variables available to browser
const useStreaming = process.env.NEXT_PUBLIC_USE_STREAMING !== "false";

// Server-only variables (not exposed)
const apiKey = process.env.SUPABASE_SERVICE_ROLE_KEY; // Server only
```

### Environment Strategies

**Local Development:**
1. Create root `.env` file (ignored by git)
2. Both apps load automatically
3. Use `npm run env:pull` to sync from Vercel

**Production (Vercel):**
1. Set env vars in Vercel dashboard
2. Automatically injected at build/runtime
3. Secrets secured (not visible in code)
4. Can override per deployment/branch

**CI/CD Integration:**
- Environment variables passed via GitHub Secrets
- Build uses provided env vars
- No hardcoded secrets in repository

---

## Data Flow & Interactions

### User Enrollment & Session Flow

```
User Loads App
    ↓
Check if participant already stored
    ├─ YES: Load session from localStorage/Supabase
    └─ NO: Show enrollment form
    ↓
Participant Fills Form
    ├─ Name input
    ├─ Group selection (A/B)
    └─ Optional: Scenario selection
    ↓
POST /api/participants (async)
    ├─ Create participant record
    └─ Update group assignment
    ↓
Chat Ready
    ├─ Display scenario context (if selected)
    └─ Focus on input for first message
```

### Message Flow (Streaming Path)

```
User Sends Message
    ↓
Input Validation
    ├─ Non-empty
    └─ Within length limits
    ↓
Add Message to UI Immediately
    ├─ User message appended to history
    └─ Show loading indicator
    ↓
Log Telemetry Events
    ├─ message_send event with duration
    └─ Async POST /api/interaction
    ↓
Initiate SSE Stream
    └─ POST /api/chat-stream with { message, session_id, ... }
    ↓
Server: Initialize Stream
    ├─ Ensure session exists
    ├─ Append user message to history
    ├─ Detect topic/intent
    └─ Send "init" event
    ↓
Client: Receive Init Event
    ├─ Extract session_id, topic, escalate
    └─ Log telemetry: reply_init event
    ↓
Server: Stream LLM Tokens
    ├─ Call OpenAI API with streaming
    ├─ Chunk text at word boundaries
    ├─ Send "token" events
    └─ Log telemetry: first_token event (with TTFT)
    ↓
Client: Accumulate Tokens
    ├─ Append token text to response
    └─ Update UI in real-time
    ↓
Server: Complete Response
    ├─ Send "done" event with full reply
    ├─ Save to session history
    └─ Log telemetry: reply_done event
    ↓
Client: Finalize Message
    ├─ Close EventSource
    ├─ Append assistant message to UI
    └─ Clear input field
    ↓
Async: Persist to Supabase
    ├─ POST /api/messages (user message)
    ├─ POST /api/messages (assistant message)
    └─ Log events to /api/interaction (batch)
```

### Feedback Submission Flow

```
User Clicks "Finish"
    ↓
Show Feedback Form Modal
    ├─ Rubric rating inputs (1-5 scale)
    │   ├─ Overall rating
    │   ├─ Task success
    │   ├─ Clarity
    │   ├─ Empathy
    │   └─ Accuracy
    ├─ Resolution status dropdown
    ├─ Comments text area
    └─ Submit button
    ↓
User Fills Form
    └─ Rating values required
    ↓
Submit Feedback
    ↓
Validate Form
    ├─ All ratings present (1-5)
    ├─ Optional: Resolution status
    └─ Optional: Comments
    ↓
POST /api/feedback
    ├─ Include session, participant, scenario
    ├─ Include all rubric ratings
    ├─ Include user-agent from browser
    └─ Include page URL
    ↓
Server: Process Feedback
    ├─ Validate request
    ├─ Log configuration diagnostics
    ├─ Insert to support_feedback table
    └─ Return success/error
    ↓
Client: Handle Response
    ├─ If success: Show confirmation
    ├─ If failure: Show error with retry
    └─ Clear form
```

### Telemetry Collection Flow

```
User Interacts with UI
    ├─ Typing in input
    ├─ Clicking suggestions
    ├─ Sending message
    └─ Other interactions
    ↓
Client Logs Event
    ├─ Determine event type
    ├─ Capture timestamp
    ├─ Measure duration (if applicable)
    └─ Include metadata
    ↓
Accumulate Events
    ├─ Buffer events in memory
    └─ Batch for efficiency
    ↓
Periodically POST /api/interaction
    ├─ Send accumulated events
    └─ Clear buffer
    ↓
Server: Process Events
    ├─ Validate each event
    ├─ Filter invalid events
    ├─ Transform timestamps (UTC)
    └─ Insert to interaction_events table
    ↓
Async: Events Logged
    ├─ Available for analysis
    └─ Can reconstruct user journey
```

### LLM Decision Tree

```
Chat Request Received
    ↓
Determine Reply Source
    ├─ IF agent._llm_client is set
    │   └─ Use LLM Path
    │       ├─ Build system prompt
    │       ├─ Gather chat history (last 6 turns)
    │       ├─ Call OpenAI API with streaming
    │       ├─ Parse tokens
    │       └─ Return streamed response
    │
    └─ ELSE
        └─ Use Rule-Based Path
            ├─ Detect topic from keywords
            ├─ Look up in knowledge base
            ├─ Return prewritten response
            └─ Add quick-reply suggestions
```

---

## Performance & Scalability

### Performance Characteristics

**Frontend Performance:**
- **Initial Load:** ~2-3s (Next.js + React)
- **Message Send:** Immediate UI update + background API call
- **Message Receive:** Real-time streaming for SSE path
- **Feedback Form:** Instant rendering

**Backend Performance:**
- **Request Latency:** 100-200ms (rule-based), 2-5s (LLM)
- **Time-to-First-Token:** 500-2000ms (LLM streaming)
- **Token Generation Rate:** 50-100 tokens/s
- **Concurrent Users:** Vercel auto-scales (no explicit limit)

**Database Performance:**
- **Inserts:** <100ms for batch operations
- **Selects:** <50ms for message retrieval (indexed)
- **Availability:** 99.9% SLA (Supabase)

### Scalability Approach

**Horizontal Scaling:**
- **Frontend:** CDN distribution, edge caching
- **Backend:** Serverless functions (auto-scaling)
- **Database:** Supabase handles replication/sharding

**Vertical Optimization:**
- Minimize LLM API calls (cache frequent responses)
- Batch write operations to Supabase
- Compress response payloads

**Caching Strategy:**
- Static assets: Browser cache (long TTL)
- API responses: Not cached (fresh for each request)
- Database: Supabase connection pooling
- LLM: Could implement semantic caching (future)

### Load Testing Estimates

**Concurrent Users:**
- **5 users:** No scalability concerns
- **50 users:** Vercel scales automatically
- **500 users:** LLM API rate limits may apply
- **5000+ users:** Requires LLM rate limit planning

**Data Volume:**
- **1000 conversations:** ~50KB Supabase storage
- **1M interactions:** ~500MB interaction_events table
- **Unlimited conversations:** Supabase scales automatically

---

## Security Design

### Input Validation

**Request Validation:**
- Pydantic models enforce type checking
- Max length limits on text fields
- Reject missing required fields
- Sanitize participant IDs

**Example (ChatRequest):**
```python
class ChatRequest(BaseModel):
    message: str  # Required, non-empty
    session_id: Optional[str] = None
    participant_group: Optional[str] = None
    # Pydantic validates type, length, format
```

**Markdown Sanitization:**
- Frontend renders markdown (React component)
- User-generated content in message display
- Markdown.tsx component sanitizes output
- No script execution in markdown

### Authentication & Authorization

**Current Model:**
- No user authentication
- Participant ID as lightweight identifier
- Group assignment for A/B testing
- No authorization checks (best-effort)

**Production Recommendations:**
- Implement session tokens if needed
- Add participant authentication
- Verify session ownership before allowing message retrieval
- Rate limit by participant ID

### Data Protection

**Data at Rest:**
- Supabase encrypts data automatically (TLS)
- Database credentials in environment variables
- No plaintext secrets in code
- RLS policies prevent unauthorized access

**Data in Transit:**
- HTTPS/TLS for all API communication
- Vercel enforces HTTPS
- Supabase connections use TLS
- OpenAI API uses TLS

**Sensitive Data:**
- API keys in environment variables only
- Never logged in plain text
- Service role key kept server-side only
- Anon key exposed to client (acceptable for anon inserts)

### CORS Policy

**Configuration:**
```python
CORS_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

**Example Values:**
- Local: `http://localhost:3000`
- Production: `https://example.com,https://www.example.com`
- Vercel auto-domain: `https://vodacare.vercel.app`

**CORS Headers:**
- `Access-Control-Allow-Origin`: Dynamically set
- `Access-Control-Allow-Methods`: GET, POST, PUT, DELETE, etc.
- `Access-Control-Allow-Headers`: All
- `Access-Control-Allow-Credentials`: true

### External API Security

**OpenAI Integration:**
- API key securely stored in env var
- Rate limiting via OpenAI account
- Token limits prevent DoS (220 tokens max per response)
- Monitored for unusual activity

**Supabase Integration:**
- Service role key for server-side operations
- Anon key for client-side operations (restricted)
- RLS policies enforce data isolation
- Connection pooling prevents exhaustion

### OWASP Top 10 Mitigations

| Vulnerability | Mitigation |
|--------------|-----------|
| Injection | Pydantic models, parameterized queries (PostgREST) |
| Broken Auth | No auth (simplified); session IDs non-secret |
| Sensitive Data | TLS in transit, encrypted at rest, env vars for secrets |
| XML External Entities | Not applicable (JSON only) |
| Broken Access Control | RLS policies, best-effort checks |
| Security Misconfiguration | Environment-driven config, no hardcoding |
| XSS | React escaping, markdown sanitization |
| Insecure Deserialization | Pydantic validation before use |
| Using Components with Known Vulns | Dependencies managed, regular updates |
| Insufficient Logging | Event logging, error diagnostics logged |

---

## Error Handling & Resilience

### Error Categories

**User-Facing Errors:**
- Invalid message (empty, too long): Show inline message
- Network error: Retry with exponential backoff
- LLM unavailable: Show friendly error in chat
- Feedback submission failed: Show error modal with retry

**System Errors:**
- Supabase unavailable: Continue without persistence (202 Accepted)
- OpenAI API error: Fall back to error message
- Session creation failed: Generate new session ID
- Database connection timeout: Return 500, don't retry

### Error Recovery Strategies

**Graceful Degradation:**
- Without LLM → rule-based responses
- Without Supabase → no persistence, UI works
- Without streaming → use non-streaming endpoint
- Without scenarios → hide scenario selector

**Retry Logic:**
```typescript
const retryWithBackoff = async (fn, maxRetries = 3) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await sleep(Math.pow(2, i) * 100); // Exponential backoff
    }
  }
};
```

**User Notification:**
- Toast messages for non-blocking errors
- Modal dialogs for critical errors
- Inline errors for form validation
- Error boundaries for React crashes

### Logging & Diagnostics

**Server-Side Logging:**
```python
logger = logging.getLogger(__name__)

# Configuration diagnostics (on feedback endpoint)
logger.warning("/api/feedback config %s", {
    "configured": store.is_configured(),
    "has_url": bool(store.url),
    "has_key": bool(store.key),
    "url_host": parsed_url,
    "key_prefix": key_prefix
})

# Error logging with context
logger.exception("Failed to persist feedback", extra={
    "session_id": session_id,
    "participant_id": participant_id,
    "table": "support_feedback"
})
```

**Client-Side Logging:**
```typescript
console.error('Message send failed', error);
logEvent('error', {
  component: 'ChatWindow',
  error_message: error.message,
  error_code: error.code
});
```

### Observability

**Metrics to Track:**
- Request latency (p50, p95, p99)
- Error rate by endpoint
- LLM token usage and cost
- Message success rate
- Session duration distribution
- Feedback submission rate

**Logging Strategy:**
- Structured logs (JSON) for easy parsing
- Include session_id, participant_id, participant_group
- Log all errors with context
- Avoid logging sensitive data (API keys)

---

## Summary

This comprehensive design document covers all aspects of the VodaCare Support platform, from high-level architecture through low-level implementation details. The system is carefully designed to support both production use and FYP research goals, with emphasis on:

1. **Flexibility:** Works with or without LLM, database, streaming
2. **Research-First:** Comprehensive telemetry and evaluation framework
3. **Simplicity:** Monolithic frontend, clean backend separation
4. **Scalability:** Serverless architecture on Vercel
5. **Security:** Best practices for data protection and API security
6. **Quality:** Human-LLM testing alignment for rigorous evaluation

The architecture enables meaningful research on the efficacy of LLM-powered support versus human interactions, with standardized evaluation metrics and comprehensive data collection for downstream analysis.
