# Coding Conventions

**Analysis Date:** 2026-02-19

## Naming Patterns

**Files:**
- TypeScript components: PascalCase (`ChatWindow.tsx`, `MessageBubble.tsx`)
- Utility/library files: camelCase (`api.ts`, `supabaseClient.ts`, `telemetry.ts`)
- Python modules: snake_case (`chat.py`, `scenarios.py`, `storage.py`)
- Config files: snake_case (`config.py`)

**Functions:**
- TypeScript: camelCase for async/sync functions (`sendMessage()`, `fetchScenarios()`, `formatStreamingText()`)
- Python: snake_case for all functions (`get_scenarios()`, `ensure_session()`, `_detect_topic()`)
- React components: PascalCase (`export default function ChatWindow()`)

**Variables:**
- TypeScript: camelCase for all (`sessionId`, `participantGroup`, `messages`, `busy`)
- Python: snake_case for module-level and function-local (`session_id`, `participant_id`, `api_key`)
- React state: camelCase with verb prefixes for functions (`setMessages`, `setBusy`, `setStarted`)
- Type aliases/discriminators: lowercase (`"user" | "assistant"` for roles)

**Types/Interfaces:**
- TypeScript: PascalCase for type names (`ChatResponse`, `StreamHandlers`, `InteractionEvent`, `ChatRequest`)
- Python Pydantic models: PascalCase (`ChatRequest`, `ChatResponse`, `FeedbackInsert`)
- Union types: snake_case literals (`"assistant" | "user"`)

## Code Style

**Formatting:**
- No explicit formatter detected (ESLint/Prettier not in web/package.json)
- Consistent manual formatting observed across files
- Indentation: 2 spaces (TypeScript/JavaScript), 4 spaces (Python)
- Line length: Generally kept under 100 characters

**Linting:**
- TypeScript: No ESLint config detected, but tsconfig.json enforces strict mode
- Strict compiler options enabled: `strict: true`, `forceConsistentCasingInFileNames: true`, `noEmit: true`
- Python: No linter config detected, but code follows PEP8 conventions

## Import Organization

**Order (TypeScript):**
1. React/Next.js framework imports (`import { useEffect, useState } from "react"`)
2. Next.js specific imports (`import { useRouter } from "next/navigation"`)
3. Local components (`import ChatWindow from "../components/ChatWindow"`)
4. Local utilities (`import { sendMessage } from "../lib/api"`)
5. Local types implicit in usage

**Order (Python):**
1. Standard library imports (`import json`, `from typing import...`)
2. Third-party imports (`from fastapi import...`, `from pydantic import...`)
3. Local app imports (`from .models import...`, `from .config import...`)

**Path Aliases:**
- TypeScript: No explicit path aliases detected, uses relative paths exclusively
- Python: sys.path modifications in `main.py` to include parent directories

## Error Handling

**Patterns:**
- TypeScript async: try-catch blocks around fetch calls, typically swallow errors with empty catch or conditional logging
- Example from `ChatWindow.tsx`: `try { ... } catch {}` for best-effort operations (localStorage, event logging)
- Example from `api.ts`: Throw on non-OK responses (`if (!res.ok) throw new Error(...)`)
- Python: try-except blocks with exception logging, often using `logger.exception()` or `logger.warning()`
- Example from `main.py`: Try-catch wraps storage operations, returns sensible defaults on failure (202/500 status codes)

**Error messages:**
- User-facing: Generic, non-technical (`"Sorry—something went wrong. Please try again."`)
- Logging: Structured with context (`"Supabase insert failed: table=%s status=%s"`)

## Logging

**Framework:**
- TypeScript: Browser `console.log()` and `console.error()` for API routes
- Python: Python standard `logging` module via `logger = logging.getLogger(__name__)`

**Patterns:**
- TypeScript: Selective logging in API route handlers (`[Feedback]`, `[Feedback API]` prefixes as context)
- Python: Structured logging with context variables (`logger.warning("message", var1, var2)`)
- Both: Try-except blocks around logging itself to prevent logging failures from breaking code
- Telemetry events: Custom `logEvent()` function for analytics, best-effort via `sendBeacon()` or fetch with `keepalive`

## Comments

**When to Comment:**
- Lightweight formatting heuristics documented inline (see `formatStreamingText()` in `ChatWindow.tsx`)
- Non-obvious algorithmic choices (e.g., SSE event parsing logic in `api.ts`)
- Conditional behavior for deployment environments (see `apiUrl()` localhost detection)
- Business rules or research-specific logic (e.g., "Participant gate", "scenario context")

**JSDoc/TSDoc:**
- Minimal usage observed
- Python docstrings used for routes (see `scenarios.py` GET endpoint with docstring and example response)
- TypeScript inline: Type annotations are primary documentation (`type Props = {...}`)

## Function Design

**Size:**
- Typical range: 20-150 lines for business logic functions
- Larger components: `ChatWindow.tsx` is 790 lines (encompasses state management + UI)
- Async operations: Wrapped in useEffect hooks with dependency tracking

**Parameters:**
- TypeScript: Explicit type annotations on all params (`message: string`, `sessionId?: string`)
- Python: Type hints on all function params and returns (`def chat(req: ChatRequest) -> ChatResponse`)
- Object destructuring common for React props (`{ role, text = "", typing = false }`)

**Return Values:**
- TypeScript async: Always Promise-wrapped for HTTP calls, explicit types on API responses
- Python: Tuple returns for operation status (`Tuple[int, int]` for inserted_count, status_code)
- React: Implicit JSX element return type

## Module Design

**Exports:**
- TypeScript: Named exports for utilities (`export async function sendMessage(...)`, `export type ChatResponse = {...}`)
- React components: Default export only (`export default function ChatWindow()`)
- Python: No explicit exports; functions called via import paths

**Barrel Files:**
- Not used; each component/utility imported directly from its file

## State Management

**TypeScript/React:**
- useState for local component state (messages, input, form fields)
- localStorage for session persistence (keys: `vc_session_id`, `vc_participant_id`, `vc_scenario_id`)
- No global state management library detected (Redux, Zustand absent)

**Python:**
- In-memory dictionaries for session storage (`self.sessions: Dict[str, List[Tuple[str, str]]]`)
- No database ORM; direct REST API calls to Supabase via requests library

## Async Patterns

**TypeScript:**
- `async/await` used exclusively (no Promise chaining)
- All event handlers wrapped in try-catch or marked as async with error boundaries
- Streaming responses parsed manually via ReadableStream API + TextDecoder

**Python:**
- `async/await` in FastAPI route handlers for streaming endpoints
- Sync route handlers for simple POST/GET operations
- AsyncGenerator type annotation for event streaming functions

## Constants and Configuration

**Patterns:**
- Environment variables via `process.env` (web) and `os.getenv()` (Python)
- Config functions wrap env access: `get_openai_api_key()`, `get_allowed_origins()`
- Fallback values provided (`NEXT_PUBLIC_USE_STREAMING !== "false"`)
- Knowledge base as nested dicts in agent (`self.knowledge: Dict[str, Dict]`)
- Scenario definitions as module-level list in `scenarios.py`

---

*Convention analysis: 2026-02-19*
