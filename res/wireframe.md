# Project Wireframe

## Overview
- Goal: Outline app structure, flows, and simple A/B testing.
- Scope: Frontend rendering, basic state, routes, and minimal backend touchpoints.

## Architecture
- Frontend: Multipage (framework-agnostic), components for layout, pages, and shared UI.
- Backend: Thin API layer for data fetch/submit. No server-driven experiments.
- Storage: LocalStorage for lightweight state (including A/B choice).
- Build/Deploy: Standard build pipeline (not specified here).

## Tech Stack (Assumptions)
- Frontend: TypeScript, NextJS
- Backend: Node.js/Express or similar lightweight HTTP service.
- DB: Lightweight store (SQLite/Postgres) depending on deployment needs.
- Infra: Containerized with Docker; deploy via simple CI to a single service.

## Data Flow
- UI triggers actions → optional API calls → local state update → re-render.
- All API calls include an `x-ab-variant` header if variant is set.

## Directory Structure
- `res/` documentation, assets (this file lives here).
- `web/` frontend app code, components, routes.
- `server/` backend HTTP service, routes, handlers.
- `shared/` shared types/utilities (DTOs, validation schemas).
- `scripts/` local dev and build scripts.

## Pages / Views
- Home: Entry point, explains product value and routes to core feature.
- Feature: Main interaction surface; conditionally renders A/B variant blocks.
- Settings: Simple page to change A/B variant (and other prefs if needed).
- Not Found: Fallback for unknown routes.

## Navigation
- Top-level nav with links to Home, Feature, Settings.
- Router handles route changes without full reloads.

## A/B Testing (Simple, User-Selected)
- Intent: Let users self-select variant A or B (no assignment logic, no bucketing). Since its just collecting data from known people.
- UI Control:
  - Persistent control in Settings: radio group: `A`, `B`, `None` (default).
  - Optional quick toggle in header for convenience.
- State Persistence:
  - Key: `ab.variant` in LocalStorage with values `"A" | "B" | null`.
  - Read at app init; fall back to `null` if missing/invalid.
- Usage in UI:
  - Conditional rendering helpers:
    - `isVariant("A")` → render A-specific components/props.
    - `isVariant("B")` → render B-specific components/props.
    - Default experience if `null`.
- Network Propagation:
  - For each API request, include header `x-ab-variant: A|B` only when set.
  - Do not block requests if absent.
- Analytics (optional):
  - Fire client events with `variant` property when meaningful actions occur.
  - No server-side experiment analysis required.
- Accessibility:
  - Radio options are labeled and focusable; toggle has clear state.

## State & Storage
- User session (if any): cookie or token (out of scope here).
- Preferences: LocalStorage keys
  - `ab.variant`: experiment choice `A|B|null`.

## Backend API
- Style: REST JSON; include `x-ab-variant` when present.
- Validation: JSON schema at the edge; reject invalid payloads.
- Auth: Optional; if enabled, bearer token via `Authorization` header.
- Rate limiting: Simple per-IP limit (if exposed publicly).

## API Endpoints
Super light weight.
- /health - check it's responding properly
- /chat - complete chats

## Data Model (Example)
- `Resource`: `{ id: string, title: string, content: string, updatedAt: string }`
- `ActionEvent`: `{ id: string, type: string, resourceId?: string, variant?: 'A'|'B'|null, ts: string }`

## Persistence
- In-memory or SQLite for local dev.

## Error Handling
- UI displays inline, human-readable messages.
- API errors do not clear A/B choice.
- Backend returns structured errors: `{ error: { code, message, details? } }`.
- Map known error classes to HTTP: 400 validation, 401 auth, 404 not found, 409 conflict, 429 rate limit, 500 unknown.

## Accessibility
- Keyboard navigation works across nav and settings controls.
- Color contrast sufficient for variant UI differences.

## Security
- Input validation on all endpoints; never trust client fields.
- Sanitize rendered HTML; prefer text-only unless sanitized.
- Store secrets in environment variables; never commit secrets.
- Apply CORS policy to allowed origins; include preflight for custom header.
- Use HTTPS in all environments beyond local.

## Performance
- Frontend: Code split feature routes; lazy-load variant-specific components.
- Cache API GETs.
- Compress responses and serve static assets with long-cache + hash.

## Observability
- Logging: Structured logs with `level`, `msg`, `traceId`, `variant` (if present).
- Metrics: Basic counters for requests, errors, action events; include `variant` label.
- Tracing: Optional HTTP span with route/method/status.

## Configuration & Environments
- `.env` for local; CI injects secrets via vault/runner vars.
- Config keys: `PORT`, `DATABASE_URL`, `LOG_LEVEL`, `ALLOWED_ORIGINS`.
- Environment: `local`

## CI/CD
- Not deployed.

## Dev Workflow
- Local: `npm run dev` runs client and server with hot reload.
- Code style: Prettier + ESLint defaults; commit hooks for lint/test.
- Branching: trunk-based or short-lived feature branches.

## Release & Versioning
- Semantic versioning for API; client is coupled but tagged per release.
- Changelog entries for user-visible changes; note variant changes explicitly.
