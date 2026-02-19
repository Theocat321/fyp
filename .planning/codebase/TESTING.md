# Testing Patterns

**Analysis Date:** 2026-02-19

## Test Framework

**Runner:**
- Not detected in production codebase
- No Jest, Vitest, Pytest, or similar test runner config present
- No test files found in `/server` or `/web` (excluding node_modules and venv)

**Run Commands:**
- No established test commands found (web/package.json has no test script)
- Manual testing via dev server: `npm run dev` (Next.js), Python via `uvicorn`

**Assertion Library:**
- Not applicable (no test framework configured)

## Test File Organization

**Location:**
- No dedicated test directory structure
- LLM testing exists in separate directory: `/Users/stagcto/fyp/llm-testing/` (excluded from main analysis)
- Production code lacks test co-location pattern

**Naming:**
- Not applicable (no test files in main codebase)

## Test Structure

Not applicable—no test framework present in main application code.

## Integration Testing Patterns

**Manual Integration:**
Code is tested through manual browser interaction and API calls. Patterns observed:

**TypeScript/Web Layer:**
- Manual testing of chat flow: enrollment form → message input → streaming response → feedback form
- LocalStorage persistence tested manually via browser dev tools
- API integration verified through network tab inspection
- Example flow in `ChatWindow.tsx`:
  ```typescript
  // Test setup: store participant/session IDs
  localStorage.setItem("vc_participant_name", participantName);
  localStorage.setItem("vc_participant_id", pid);

  // Test message flow
  setMessages((m) => [...m, { role: "user", text: trimmed }]);
  // Call API
  const resp: ChatResponse = await sendMessage(trimmed, sid, participantGroup, pid);
  // Verify response
  setMessages((m) => [...m, { role: "assistant", text: resp.reply }]);
  ```

**Python/Server Layer:**
- Health check endpoint for diagnostics: `GET /api/health` returns provider and storage config status
- Streaming endpoint tested via curl or browser fetch with event-stream headers
- Storage operations wrapped in try-except with status code returns for verification
- Example from `main.py` feedback endpoint:
  ```python
  stored, code = store.insert_rows("support_feedback", [row])
  status = 200 if stored else (code if code else 202)
  if not stored:
    if not store.is_configured():
      return JSONResponse({"ok": False, "error": "supabase_not_configured"}, status_code=500)
  ```

## Mocking

**Framework:** Not applicable (no test framework)

**Manual Mocking Observed:**
- LLM client optional initialization with graceful fallback to rule-based mode
  ```python
  if api_key:
    try:
      from openai import OpenAI
      self._llm_client = OpenAI(api_key=api_key, base_url=base_url)
    except Exception:
      self._llm_client = None
  ```
- Supabase storage optional: `if not self.is_configured()` checks skip writes, return 202 status
- Environment-based behavior: `ASSISTANT_MODE` determines rule-based vs. LLM mode

**What to Mock (if tests added):**
- Supabase REST API responses (success/conflict/error)
- OpenAI client streaming responses
- localStorage (via jest.mock or similar)
- fetch API (via MSW or jest.mock)
- Date/time for telemetry timestamps

**What NOT to Mock:**
- Session/message storage logic (in-memory dicts are single-instance)
- Topic detection (rule-based, no external deps)
- Text formatting functions (pure functions)

## Fixtures and Test Data

**Scenario Data:**
- Static scenarios defined in `server/api/scenarios.py` as module-level list:
  ```python
  SCENARIOS = [
    {"id": "scenario_001_esim_setup", "name": "eSIM Setup", ...},
    {"id": "scenario_002_roaming_activation", "name": "EU Roaming Activation", ...},
    ...
  ]
  ```
- Served via `GET /api/scenarios` for UI test scenario selection

**Test Scenarios:**
Structured scenarios for research testing (not automated tests but manual test cases):
- `scenario_001_esim_setup`: Device/eSIM topic
- `scenario_002_roaming_activation`: Roaming topic
- `scenario_003_billing_dispute`: Billing topic
- `scenario_004_plan_upgrade`: Plans topic
- `scenario_005_network_issue`: Network topic

**Message/Participant Fixtures:**
- Participant enrollment form generates UUIDs at runtime
- Sample participant flow: `name`, `group` (A/B), optional `scenario_id`
- Messages stored via API: `{ session_id, role, content, participant_id, participant_name, participant_group }`

## Coverage

**Requirements:** Not enforced (no test config present)

**View Coverage:** Not applicable

## Test Types

**Unit Tests:**
- Not present in codebase
- If added, candidates: `formatStreamingText()`, `_detect_topic()`, topic/role detection logic

**Integration Tests:**
- Not automated; manual via browser and curl
- Critical paths: chat flow, feedback submission, Supabase writes

**E2E Tests:**
- Not detected in main codebase
- Separate LLM evaluation suite exists in `/llm-testing/` (Python-based scenario evaluation)

**Streaming Response Tests:**
- Server-sent events (SSE) parsed in `web/lib/api.ts` via ReadableStream API
- Manual testing via browser with event-stream response inspection
- Chunking logic in `_chunk_text_for_stream()` tested manually via UI observation

## Error Handling Testing

**Pattern Observed (best-effort telemetry):**
```typescript
try {
  await logEvent({ session_id, event: "send", ... });
} catch {}
```
- Errors swallowed; logging failures do not break application
- Applied to all telemetry and storage operations marked as "best-effort"

**Pattern for API Failures:**
```python
try:
  result = agent.chat(req.message, req.session_id, ...)
except Exception:
  logger.exception("LLM chat failed")
  return JSONResponse({ "reply": "error message", ... }, status_code=500)
```
- Exceptions logged, user-friendly error response returned

## Testing Best Practices to Implement

If automated tests are added, follow these patterns observed in code:

**Async Testing:**
```typescript
// Pattern: await with try-catch for async operations
try {
  const resp = await sendMessage(text, sid);
  expect(resp.reply).toBeDefined();
} catch (e) {
  // Handle or verify error
}
```

**Resilience Testing:**
```python
# Pattern: test both configured and unconfigured states
store = SupabaseStore()
assert store.is_configured() == bool(url and key)
stored, code = store.insert_rows(...)
assert code in [200, 202]  # Accept both success and benign failure
```

**Event Streaming:**
```typescript
// Pattern: parse SSE events manually
const reader = res.body.getReader();
const decoder = new TextDecoder();
let buffer = "";
while ((idx = buffer.indexOf("\n\n")) !== -1) {
  const rawEvent = buffer.slice(0, idx);
  // Parse event type and data from SSE format
  const lines = rawEvent.split(/\r?\n/);
  for (const line of lines) {
    if (line.startsWith("event:")) eventType = line.slice(6).trim();
    if (line.startsWith("data:")) dataLines.push(line.slice(5));
  }
}
```

## Current Test Coverage Gaps

**Critical untested areas:**
- Chat message flow: user input → API call → response storage → UI update
- Streaming token accumulation and formatting
- Feedback form submission and Supabase write
- Participant enrollment and localStorage persistence
- Session recovery across page reloads
- LLM fallback to rule-based mode when configured
- Storage layer Supabase REST calls and error handling

---

*Testing analysis: 2026-02-19*
