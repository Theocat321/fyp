# Codebase Concerns

**Analysis Date:** 2026-02-19

## Tech Debt

**Excessive Silent Error Handling:**
- Issue: Throughout the codebase, errors are swallowed with empty `catch {}` blocks and `try {} catch {}` patterns. This obscures bugs and makes debugging difficult.
- Files: `web/components/ChatWindow.tsx` (lines 99, 123, 144, 154, 165, 182, 196, 226, and 50+ more), `web/lib/api.ts` (line 111), `web/lib/telemetry.ts` (line 44)
- Impact: Failed API calls, storage operations, and telemetry events go unlogged, making it impossible to diagnose production issues. Users won't know if their data is being saved.
- Fix approach: Replace silent catches with: (1) conditional logging based on environment (dev vs prod), (2) fallback behavior specification, (3) metrics collection for monitoring failure rates. At minimum, log non-auth errors to console in development.

**Hardcoded Environment Variable Fallback Logic:**
- Issue: Multiple environment variables use fallback chains (e.g., `SUPABASE_URL || NEXT_PUBLIC_SUPABASE_URL`) scattered across the codebase rather than centralized.
- Files: `web/app/api/feedback/route.ts` (lines 9-10), `server/app/config.py` (lines 44, 48)
- Impact: Unclear which env var is authoritative, difficult to audit configuration at a glance, risk of using wrong credentials in wrong context (e.g., anon key where service role key is needed).
- Fix approach: Centralize all env var resolution in a single config module. Make explicit which keys are required vs optional, and validate at startup rather than at runtime.

**Duplicate Agent/Knowledge Configuration:**
- Issue: The same knowledge base, topic detection, and suggestion logic is duplicated between `web/lib/agent.ts` and `server/app/agent.py`. Changes must be synchronized manually.
- Files: `web/lib/agent.ts` (lines 12-90), `server/app/agent.py` (lines 44-129)
- Impact: Risk of inconsistency between frontend (rule-based fallback) and backend behavior. If one is updated, the other may behave differently for the same input.
- Fix approach: Move single source of truth for knowledge to backend, or share config file (JSON) that both reference. Document which system is authoritative for each decision.

**Inconsistent Data Validation Between Frontend and Backend:**
- Issue: The feedback form (`web/components/ChatWindow.tsx` lines 42-60) has many optional fields, but no client-side validation. The backend (`server/app/models.py` lines 53-68) accepts all as nullable without constraints.
- Files: `web/components/ChatWindow.tsx` (feedback form state), `server/app/models.py` (FeedbackInsert model), `web/app/api/feedback/route.ts` (no validation)
- Impact: Invalid data (e.g., rating_overall=0 when should be 1-5, or null values when required) is silently accepted and stored. Database constraints exist but aren't surfaced as errors. Research data quality is compromised.
- Fix approach: Add Pydantic validators in models.py to enforce rating ranges (1-5). Add client-side validation in ChatWindow before submission. Return 400 with clear error messages for invalid ratings.

**In-Memory Session Storage Without Cleanup:**
- Issue: The Python FastAPI backend stores chat history in `agent.sessions` dictionary (in-memory). Sessions are never cleaned up, causing memory leak in serverless functions.
- Files: `server/app/agent.py` (line 24), `server/app/main.py` (lines 269, 326, 392)
- Impact: In serverless deployments (where function instances persist), memory usage grows unbounded with each new session. After hours of heavy use, the process exhausts memory.
- Fix approach: Implement session TTL with automatic cleanup (e.g., purge sessions older than 24 hours), or migrate session storage entirely to Supabase with lazy-loading pattern. Add memory metrics to track this.

**No Input Sanitization for User Messages:**
- Issue: User messages are passed directly to OpenAI API and stored in database without sanitization. No checks for prompt injection, excessive length, or malicious content.
- Files: `web/lib/api.ts` (line 34), `server/app/main.py` (line 329), `web/app/api/feedback/route.ts` (line 6)
- Impact: Potential for prompt injection attacks or abuse. Users could craft messages to break the system, extract internal prompts, or cause high token usage. Feedback comments could contain SQL injection if database isn't parameterized (it is, via Supabase, but principle still applies).
- Fix approach: Implement message length limits (e.g., max 1000 chars). Add basic validation for suspicious patterns. Log and rate-limit users sending very long or unusual messages.

**Supabase Service Role Key Exposed in Frontend:**
- Issue: Feedback API route (`web/app/api/feedback/route.ts` line 10) can fall back to using `NEXT_PUBLIC_SUPABASE_ANON_KEY` if `SUPABASE_SERVICE_ROLE_KEY` is not set. The anon key is public and limited, but the pattern encourages misuse.
- Files: `web/app/api/feedback/route.ts` (line 10), `web/lib/supabaseClient.ts` (line 4)
- Impact: If service role key is misconfigured, the code silently downgrades to anon key, which may have insufficient permissions. Debugging is hard because no error is raised.
- Fix approach: Make service role key required in feedback API. Fail fast at startup if not present. Remove the fallback to anon key. Document that feedback API is server-only and requires server credentials.

## Known Bugs

**Feedback Form Data Loss on Redirect:**
- Issue: After feedback submission, `ChatWindow.tsx` redirects to `/` with `window.location.href`. Browser navigation loses the form state before the redirect confirms completion.
- Files: `web/components/ChatWindow.tsx` (line 692, 781)
- Symptoms: User submits feedback, sees confirmation screen, then page redirects. If network is slow, the redirect might happen before the server confirms the submission was saved. Users may not know if feedback was received.
- Trigger: Submit feedback form and immediately close browser or navigate away
- Workaround: Wait for "Thanks for your feedback!" message before closing

**Chat History Not Preserved Across Sessions:**
- Issue: When a user reloads the page, `ChatWindow.tsx` attempts to fetch past messages with `fetchMessages()` (`lib/api.ts` line 129), but this only works if Supabase is configured. Without Supabase, messages are lost.
- Files: `web/components/ChatWindow.tsx` (lines 89-101), `web/lib/api.ts` (line 129)
- Symptoms: User reloads page and sees empty chat window even though they had a conversation
- Trigger: Chat with Supabase disabled, then reload the page
- Workaround: Configure Supabase to enable message persistence

**Scenario Context Not Displayed When Switching Groups:**
- Issue: If a participant changes their group in the enrollment form and scenario context is displayed for group A, then switches to group B, the scenario context from group A may still be visible momentarily.
- Files: `web/components/ChatWindow.tsx` (lines 450-477)
- Symptoms: Stale scenario context displayed briefly after group change
- Trigger: Select a scenario, change group, then change back
- Workaround: Clear scenario and re-select it

**Streaming SSE Parser Brittle with Malformed Events:**
- Issue: The SSE parser in `lib/api.ts` (lines 89-122) splits on `\n\n` but doesn't handle incomplete events at buffer boundaries gracefully. If the server sends an incomplete event before closing, it may not be parsed.
- Files: `web/lib/api.ts` (lines 89-122)
- Symptoms: Last few tokens of a streamed response may not be displayed
- Trigger: Network interruption during streaming
- Workaround: Response fallback shows error message instead

## Security Considerations

**Participant ID and Session ID Generation Using Weak Random:**
- Risk: Fallback ID generation uses `Math.random()` if `crypto.randomUUID()` is not available (e.g., older browsers).
- Files: `web/components/ChatWindow.tsx` (lines 140-142, 150-152)
- Current mitigation: Modern browsers support crypto.randomUUID(); fallback is for compatibility only. IDs are not sensitive credentials.
- Recommendations: Remove fallback entirely (require modern browser support). Or use a cryptographically secure library if compatibility is needed.

**No CSRF Protection on API Routes:**
- Risk: Feedback submission (`web/app/api/feedback/route.ts`) and other mutations don't validate CSRF tokens. A malicious site could submit feedback on behalf of a user.
- Files: `web/app/api/feedback/route.ts`, `web/app/api/scenarios/route.ts`
- Current mitigation: Only POST to feedback endpoint; other routes are read-only. API endpoints don't modify user accounts, only store research data.
- Recommendations: Add CSRF token validation middleware if deploying to untrusted domains. For now, acceptable for internal research use.

**Participant Data Stored Without Encryption:**
- Risk: Participant names, feedback ratings, and interaction events are stored in plain text in Supabase.
- Files: All Supabase inserts in `server/app/main.py` (lines 160-180, 213)
- Current mitigation: This is research data, not sensitive PII. Participant names are self-reported.
- Recommendations: If deployed for real customer support, add encryption at rest. Consider pseudonymization of participant names.

**OpenAI API Key Exposed in Environment:**
- Risk: `OPENAI_API_KEY` is read by `server/app/config.py` and used to initialize the OpenAI client. If the API key leaks, attackers can make API calls on the account's dime.
- Files: `server/app/config.py` (line 26), `server/app/agent.py` (line 38)
- Current mitigation: Key is server-side only, not sent to browser. Vercel/cloud provider should have secure env var storage.
- Recommendations: Use OpenAI API key rotation. Monitor API usage for unusual patterns. Consider using a dedicated lower-quota API key for development.

## Performance Bottlenecks

**Synchronous Requests in SupabaseStore:**
- Problem: All Supabase operations use `requests` library (synchronous), blocking the event loop.
- Files: `server/app/storage.py` (lines 44, 74, 113)
- Cause: Python requests library is blocking. In FastAPI async routes, this can bottleneck under load.
- Improvement path: Replace `requests` with `httpx` async client, or use Supabase async SDK if available. This would allow concurrent requests without blocking.

**Full Chat History Reloaded on Every Message:**
- Problem: Each time a user sends a message, the frontend doesn't store local history persistently. On page reload, it must refetch all messages via `GET /api/messages`.
- Files: `web/components/ChatWindow.tsx` (lines 89-101)
- Cause: History is React state, not IndexedDB or localStorage. No pagination or lazy-loading.
- Improvement path: Persist message history to localStorage with IndexedDB as fallback. Implement pagination for large histories. Only fetch new messages since last sync.

**LLM Temperature Hardcoded for All Users:**
- Problem: Temperature is hardcoded based on assistant mode (0.5 for "open", 0.3 for "strict") with no per-user control.
- Files: `server/app/main.py` (line 334)
- Cause: A/B testing groups (A/B) should be able to test different temperature settings but can't.
- Improvement path: Add temperature to participant group config. Allow experiments to define temperature per variant.

**No Caching of Scenarios Data:**
- Problem: `fetchScenarios()` is called on every page load, fetching from `/api/scenarios` which returns hardcoded array.
- Files: `web/lib/api.ts` (line 136), `web/components/ChatWindow.tsx` (lines 127-136)
- Cause: Scenarios are static but fetched every mount
- Improvement path: Cache scenarios in localStorage or React Context. Only fetch on app initialization or after a cache invalidation event.

## Fragile Areas

**ChatWindow Component Complexity:**
- Files: `web/components/ChatWindow.tsx` (790 lines)
- Why fragile: The ChatWindow component is monolithic and handles: enrollment, scenario selection, message sending, streaming, feedback collection, telemetry, and state management. Any change to one feature risks breaking others.
- Safe modification: Break into smaller components: `<EnrollmentForm>`, `<ChatArea>`, `<FeedbackModal>`. Each should manage its own state. Use custom hooks for telemetry logic.
- Test coverage: No unit tests visible. Component behavior is difficult to test in isolation.

**Agent Topic Detection Regex-Based:**
- Files: `web/lib/agent.ts` (lines 92-102), `server/app/agent.py` (similar)
- Why fragile: Topic detection uses keyword regex matching. If keywords are added/removed or new topics added, both frontend and backend must be updated. No tests ensure consistency.
- Safe modification: Extract keyword map to external JSON config. Add unit tests for each topic's keywords. Test false-positive scenarios.
- Test coverage: No visible tests for topic detection

**Streaming Response Buffering:**
- Files: `web/lib/api.ts` (lines 81-122)
- Why fragile: SSE event buffering with string concatenation is error-prone. Malformed events can cause parsing failures. No error recovery for corrupted streams.
- Safe modification: Use a proven SSE library instead of manual parsing. Add strict validation for event format. Log parsing errors for debugging.
- Test coverage: No visible tests for edge cases like incomplete events, duplicate events, or out-of-order events.

**Supabase REST API Direct Calls:**
- Files: `server/app/storage.py` (lines 41-129)
- Why fragile: SupabaseStore constructs REST endpoints manually, building query strings by hand. If Supabase API changes or if complex queries are needed (joins, filters), the code breaks.
- Safe modification: Use Supabase Python async SDK instead of raw requests. Migrate to PostgREST SDK if available.
- Test coverage: No tests for database operations. Hard to mock.

## Scaling Limits

**In-Memory Session Storage (Already Noted as Debt):**
- Current capacity: Each session stores 6 most recent messages (backend limits history). With ~100 concurrent users, ~1200 message tuples in memory.
- Limit: On Vercel serverless or long-running instances, no automatic cleanup. After days of use, memory grows to gigabytes.
- Scaling path: Move session history to Supabase entirely. Use efficient pagination. Implement TTL-based cleanup.

**No Rate Limiting on API Routes:**
- Current capacity: Any client can send unlimited requests to `/api/chat`, `/api/feedback`, `/api/interaction`.
- Limit: Sustained abuse (e.g., hammering `/api/chat` in a loop) will exhaust OpenAI quota or Supabase bandwidth.
- Scaling path: Implement rate limiting middleware (e.g., by session_id or IP). Add request validation to reject obviously malformed requests early.

**Single Supabase Project for All Environments:**
- Current capacity: All data (dev, testing, production) goes to same Supabase tables.
- Limit: As testing scales, tables become polluted with test data. Difficult to analyze real usage. Risk of accidentally deleting test data with production.
- Scaling path: Use separate Supabase projects for dev/test/prod. Or implement data tagging/filters to isolate environments in one project.

## Dependencies at Risk

**Next.js 14.2.15 (Pinned):**
- Risk: Relatively old version (released mid-2024). Security patches may not be backported forever.
- Impact: If a critical vulnerability is found, might be forced to upgrade to Next.js 15, which could have breaking changes.
- Migration plan: Pin to latest Next.js 14.x for security updates. Plan upgrade to Next.js 15 when stable.

**Python 3.10+ Requirement:**
- Risk: Python 3.10 is EOL in October 2026. Code uses modern Python features (type hints with `|` union syntax).
- Impact: After October 2026, running on Python 3.10 will no longer receive security patches.
- Migration plan: Upgrade to Python 3.11 or 3.12 within the next year. Test compatibility.

**OpenAI SDK 4.63.0:**
- Risk: OpenAI SDK versions update frequently. No major version constraint is set.
- Impact: Dependency drift could cause incompatibilities if installed on a new system.
- Migration plan: Pin to `openai~=4.63.0` to allow patch updates but prevent major version bumps.

## Missing Critical Features

**No User Authentication:**
- Problem: System relies on participant_id which is client-generated or localStorage-based. No way to verify a user is who they claim.
- Blocks: Cannot prevent the same person from enrolling multiple times. Cannot ensure data integrity for research.
- Workaround: For internal research, document that data assumes honest participants.

**No Request Authentication/Authorization:**
- Problem: All API endpoints are unprotected. Anyone can POST to `/api/feedback`, `/api/messages`, etc. if they guess the URL.
- Blocks: Cannot prevent external spam or vandalism of research data.
- Workaround: Rely on URL obfuscation and rate limiting at infrastructure level (Vercel deployment).

**No Audit Trail:**
- Problem: Who submitted feedback? When? From what IP? No audit log of changes.
- Blocks: Cannot investigate suspicious submissions or support disputes.
- Workaround: Parse Supabase audit logs (if enabled) manually.

**No Data Export/Analysis Tools:**
- Problem: Raw data is in Supabase but no built-in dashboard, export, or analysis tools.
- Blocks: Researchers must write custom SQL queries or export tables manually.
- Workaround: Write Python scripts in `llm-testing/` to query Supabase and generate reports.

## Test Coverage Gaps

**No Unit Tests for Frontend Components:**
- What's not tested: ChatWindow, MessageBubble, Markdown components. No tests for enrollment flow, message sending, feedback submission.
- Files: `web/components/*.tsx`
- Risk: Refactoring is risky. Edge cases (empty messages, network failures, rapid clicks) may not be caught until production.
- Priority: High - Frontend is user-facing and fragile (790 line monolith)

**No Unit Tests for Backend API Routes:**
- What's not tested: Chat, chat-stream, feedback, participants, messages endpoints. No tests for error handling, validation, Supabase integration.
- Files: `server/app/main.py`, `server/app/agent.py`
- Risk: Breaking changes in schema or logic are caught only manually or in production.
- Priority: High - API is data-critical

**No Integration Tests:**
- What's not tested: Full flow from UI to backend to Supabase. SSE streaming end-to-end. Feedback form submission flow.
- Risk: Issues at API boundaries are caught late.
- Priority: Medium - Can be added as codebase matures

**No Performance Tests:**
- What's not tested: Streaming latency, time-to-first-token, concurrent user load, database query performance.
- Risk: Deployment surprises when scaling.
- Priority: Medium - Test on staging before production scaling

**Streaming Logic Not Tested:**
- What's not tested: SSE parser in `lib/api.ts`, buffer edge cases, incomplete events, malformed JSON in events.
- Files: `web/lib/api.ts` (lines 81-122)
- Risk: Streaming failures in production go undetected until users report.
- Priority: Medium

---

*Concerns audit: 2026-02-19*
