# Complete Data Pipelines: Human vs LLM Users

Understanding how data flows from initial interaction → database storage → evaluation → analysis.

---

## Pipeline 1: Human Users (Real Data)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     1. USER INTERACTION                             │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    Real person uses web interface
                    Opens: http://localhost:3000
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     2. FRONTEND (React)                              │
│  - User types message in chat window                                │
│  - Clicks send                                                      │
│  - session_id generated (or existing)                               │
│  - participant_group assigned (A or B)                              │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    POST /api/chat with:
                    {
                      message: "I need help...",
                      session_id: "sess_abc123",
                      participant_group: "A"
                    }
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     3. BACKEND (FastAPI)                             │
│  /api/chat endpoint:                                                │
│  - Receives user message                                            │
│  - Loads system prompt for variant A or B                           │
│  - Calls OpenAI with conversation history                           │
│  - Gets assistant response                                          │
│  - Stores in memory ONLY (sessions dict)                            │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    Response: { reply: "...", suggestions: [...] }
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     4. FRONTEND LOGS TO DB                           │
│  Frontend makes separate API calls:                                 │
│  - POST /api/participants (on first message)                        │
│  - POST /api/messages (for user message)                            │
│  - POST /api/messages (for assistant response)                      │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     5. DATABASE (Supabase)                           │
│                                                                      │
│  participants table:                                                │
│  ┌──────────────┬──────────┬───────┬────────────┐                  │
│  │participant_id│ name     │ group │ session_id │                  │
│  ├──────────────┼──────────┼───────┼────────────┤                  │
│  │ user_001     │ John Doe │  A    │ sess_abc   │                  │
│  └──────────────┴──────────┴───────┴────────────┘                  │
│                                                                      │
│  messages table:                                                    │
│  ┌────────────┬──────────────┬──────┬─────────┬─────────────┐      │
│  │ session_id │participant_id│ role │ content │ created_at  │      │
│  ├────────────┼──────────────┼──────┼─────────┼─────────────┤      │
│  │ sess_abc   │ user_001     │ user │ "Help"  │ 2026-01-28  │      │
│  │ sess_abc   │ user_001     │ asst │ "Sure"  │ 2026-01-28  │      │
│  └────────────┴──────────────┴──────┴─────────┴─────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
                                   │
            Data sits here until you export it
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     6. EXPORT FOR EVALUATION                         │
│  Run: python3 export_real_users.py                                 │
│                                                                      │
│  - Connects to Supabase                                             │
│  - Fetches: SELECT * FROM messages                                  │
│  - Filters: WHERE session_id NOT LIKE 'sim_%'                       │
│  - Exports: real_conversations.csv                                  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     7. EVALUATION (Same as LLM!)                     │
│  Run: python3 evaluate_real_users.py --csv real_conversations.csv  │
│                                                                      │
│  - Groups messages by session_id                                    │
│  - Creates transcript structure                                     │
│  - LLM Judge (GPT-4) evaluates ──────────┐                         │
│  - Heuristic checks validate     │        │                         │
│  - Produces scores                        │                         │
└───────────────────────────────────────────┼─────────────────────────┘
                                            │
                                            │  Same evaluation
                                            │  pipeline used!
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     8. OUTPUT                                        │
│  real_user_evaluation.json:                                         │
│  {                                                                   │
│    "summary": {                                                      │
│      "avg_empathy": 0.72,                                           │
│      "avg_task_success": 0.78,                                      │
│      ...                                                             │
│    },                                                                │
│    "conversations": [...]                                            │
│  }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Pipeline 2: LLM Users (Simulated Data)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     1. EXPERIMENT SETUP                              │
│  Run: python3 run_experiment.py                                    │
│       --variant A                                                   │
│       --personas persona_01,persona_02                              │
│       --scenarios scenario_005                                      │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     2. EXPERIMENT RUNNER                             │
│  ExperimentRunner:                                                  │
│  - Loads personas from data/personas/*.yaml                         │
│  - Loads scenarios from data/scenarios/*.yaml                       │
│  - Initializes: UserSimulator, Orchestrator, Evaluators             │
│  - Loops: for each persona × scenario                               │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     3. CONVERSATION ORCHESTRATOR                     │
│  For each conversation:                                             │
│  - Creates session_id: "sim_persona_01_scenario_005_43"            │
│  - Creates participant_id: "llm_test_43"                            │
│  - Registers participant in DB                                      │
│  - Starts multi-turn conversation loop                              │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    Turn 1, 2, 3... until termination
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     4. EACH TURN                                     │
│                                                                      │
│  A) USER SIMULATOR (OpenAI GPT-4o-mini)                             │
│     - Turn 1: Uses persona.seed_utterance                           │
│     - Turn N: Generates response based on:                          │
│       * Persona characteristics                                     │
│       * Scenario context                                            │
│       * Conversation history                                        │
│       * Seeded for reproducibility                                  │
│     Output: User message                                            │
│                                                                      │
│  B) API CLIENT → VODACARE BACKEND                                   │
│     - POST /api/chat with user message                              │
│     - Backend loads system prompt (A or B)                          │
│     - Calls OpenAI for assistant response                           │
│     - Returns response                                              │
│                                                                      │
│  C) STORE TO DATABASE                                               │
│     - POST /api/messages (user message) ────┐                      │
│     - POST /api/messages (assistant msg) ───┤                      │
│                                              │                      │
│  D) CHECK TERMINATION                        │                      │
│     - Max turns? (10)                        │                      │
│     - User satisfied? ("thanks")             │                      │
│     - Escalation requested?                  │                      │
│     - Patience exceeded?                     │                      │
│     - If yes → end conversation              │                      │
│     - If no → next turn                      │                      │
└──────────────────────────────────────────────┼─────────────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     5. DATABASE (Supabase)                           │
│                                                                      │
│  participants table:                                                │
│  ┌──────────────┬──────────────────┬───────┬────────────────┐      │
│  │participant_id│ name             │ group │ session_id     │      │
│  ├──────────────┼──────────────────┼───────┼────────────────┤      │
│  │ llm_test_43  │ Simulated: Marcus│  A    │ sim_persona... │      │
│  └──────────────┴──────────────────┴───────┴────────────────┘      │
│                                                                      │
│  messages table:                                                    │
│  ┌────────────────────┬──────────────┬──────┬─────────┬──────┐     │
│  │ session_id         │participant_id│ role │ content │ ...  │     │
│  ├────────────────────┼──────────────┼──────┼─────────┼──────┤     │
│  │ sim_persona_01_... │ llm_test_43  │ user │ "Signal"│ ...  │     │
│  │ sim_persona_01_... │ llm_test_43  │ asst │ "I feel"│ ...  │     │
│  └────────────────────┴──────────────┴──────┴─────────┴──────┘     │
│                                                                      │
│  🔑 Key difference: session_id starts with "sim_"                   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     6. IMMEDIATE EVALUATION                          │
│  (Happens right after conversation, not exported)                   │
│                                                                      │
│  A) LLM JUDGE (OpenAI GPT-4)                                        │
│     Input:                                                          │
│     - Full conversation transcript                                  │
│     - Persona characteristics                                       │
│     - Scenario success criteria                                     │
│     - Evaluation rubric                                             │
│                                                                      │
│     Process:                                                        │
│     - Builds evaluation prompt                                      │
│     - Calls GPT-4                                                   │
│     - Parses scores for 3 dimensions:                               │
│       * Task Success (0.0-1.0)                                      │
│       * Clarity (0.0-1.0)                                           │
│       * Empathy (0.0-1.0)                                           │
│     - Calculates weighted overall score                             │
│     - Extracts rationale                                            │
│                                                                      │
│  B) HEURISTIC CHECKS                                                │
│     - No hallucinated plans (validates against catalog)             │
│     - No contradictions across turns                                │
│     - Appropriate response length (30-400 words)                    │
│     - Escalation when appropriate                                   │
│                                                                      │
│  Output:                                                            │
│     - EvaluationScores object                                       │
│     - HeuristicResults object                                       │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     7. ARTIFACT CREATION                             │
│  ConversationRun:                                                   │
│  - run_id: "run_exp_123_001"                                        │
│  - persona_id: "persona_01_frustrated_commuter"                     │
│  - scenario_id: "scenario_005_network_issue"                        │
│  - variant: "A"                                                     │
│  - transcript: [list of turns]                                      │
│  - llm_evaluation: {scores}                                         │
│  - heuristic_results: {checks}                                      │
│  - termination: {reason, details}                                   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                      Repeat for all persona × scenario
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     8. AGGREGATE & SAVE                              │
│  After all conversations complete:                                  │
│                                                                      │
│  - Compute SummaryStatistics:                                       │
│    * Average scores across all dimensions                           │
│    * Success rates                                                  │
│    * Termination reason breakdown                                   │
│    * Scores by persona                                              │
│    * Scores by scenario                                             │
│                                                                      │
│  - Create ExperimentRun object                                      │
│                                                                      │
│  - Write to JSON:                                                   │
│    * outputs/exp_A_smoke_test_a_20260128.json (full)               │
│    * outputs/summary_A_smoke_test_a_20260128.json (summary)        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Differences: Human vs LLM Pipeline

| Aspect | Human Users | LLM Users |
|--------|-------------|-----------|
| **User Input** | Real person typing | GPT-4o-mini generates based on persona |
| **Session ID** | `sess_abc123` | `sim_persona_01_scenario_005_43` |
| **Participant ID** | `user_001` | `llm_test_43` |
| **DB Storage** | Frontend logs after conversation | API client logs during conversation |
| **Evaluation** | **Export → Evaluate separately** | **Evaluate immediately after each conversation** |
| **Persona Context** | Unknown (inferred post-hoc) | Known (defined in YAML) |
| **Scenario Context** | Unknown (support topic) | Known (defined in YAML) |
| **Reproducibility** | Not reproducible | Seeded, reproducible |

---

## Critical: Same Evaluation Pipeline

**Both pipelines converge at evaluation:**

```
Human Conversations               LLM Conversations
       │                                 │
       │ (export & group)                │ (already grouped)
       │                                 │
       └────────────┬────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   SAME EVALUATION     │
        │   ----------------    │
        │   • LLM Judge (GPT-4) │
        │   • Heuristic Checks  │
        │   • Same Rubric       │
        │   • Same Weights      │
        └───────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
   Human Scores            LLM Scores
   {empathy: 0.72}        {empathy: 0.90}
                    │
                    ▼
             Statistical Comparison
             t-test, ANOVA, etc.
```

---

## Data Flow Summary

### Human Users
1. **Live interaction** → Browser
2. **Chat happens** → Frontend ↔ Backend
3. **Messages stored** → Database (async by frontend)
4. **Later: Export** → CSV file
5. **Later: Evaluate** → JSON results

### LLM Users
1. **Batch creation** → CLI command
2. **Simulation runs** → UserSimulator → Backend
3. **Messages stored** → Database (sync by API client)
4. **Immediate evaluation** → Built into runner
5. **Instant results** → JSON artifacts

---

## Database Schema

```sql
-- participants table
CREATE TABLE participants (
  participant_id TEXT PRIMARY KEY,
  name TEXT,
  "group" TEXT,  -- 'A' or 'B'
  session_id TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- messages table
CREATE TABLE messages (
  id SERIAL PRIMARY KEY,
  session_id TEXT NOT NULL,
  participant_id TEXT,
  participant_group TEXT,
  role TEXT,  -- 'user' or 'assistant'
  content TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Query to see all conversations
SELECT session_id, COUNT(*) as message_count
FROM messages
GROUP BY session_id
ORDER BY message_count DESC;

-- Filter simulated vs real
SELECT
  CASE
    WHEN session_id LIKE 'sim_%' THEN 'simulated'
    ELSE 'real'
  END as user_type,
  COUNT(DISTINCT session_id) as sessions,
  COUNT(*) as messages
FROM messages
GROUP BY user_type;
```

---

## Evaluation Rubric (Applied to Both)

```yaml
Task Success (60% weight):
  - Did conversation achieve goal?
  - Were questions answered?
  - Clear path forward provided?

Clarity (20% weight):
  - Language appropriate for user?
  - Information digestible?
  - Technical terms explained?

Empathy (20% weight):
  - Tone matched user's emotion?
  - Acknowledged frustration?
  - Professional yet human?
```

---

## Why This Design?

### Advantages
1. **Fair Comparison**: Same evaluation criteria for both
2. **Reproducible**: LLM conversations are seeded
3. **Traceable**: All data in database
4. **Flexible**: Can re-evaluate with different rubric
5. **Scalable**: Batch process many personas/scenarios

### For Your Dissertation
You can confidently claim:

> "To ensure valid comparison between experimental conditions, both real
> and simulated user conversations were evaluated using identical assessment
> criteria. All conversations were scored by a GPT-4-based judge using a
> standardized rubric (task success 60%, clarity 20%, empathy 20%),
> supplemented by deterministic heuristic safety checks. This methodology
> eliminates evaluator bias and ensures statistical validity when comparing
> system prompt variants."

---

## Verification Commands

### Check database has both types
```sql
SELECT
  CASE WHEN session_id LIKE 'sim_%' THEN 'Simulated' ELSE 'Real' END as type,
  participant_group as variant,
  COUNT(DISTINCT session_id) as conversations
FROM messages
GROUP BY type, variant;
```

### Compare evaluation outputs
```bash
# View simulated results
cat outputs/summary_A_smoke_test_*.json | jq '.summary'

# View real user results (after export & evaluation)
cat outputs/real_user_evaluation.json | jq '.summary'
```

### Statistical comparison
```python
import json
from scipy import stats

# Load both
sim = json.load(open('outputs/summary_A_*.json'))
real = json.load(open('outputs/real_user_evaluation.json'))

# Compare empathy scores
sim_empathy = sim['summary']['avg_empathy']
real_empathy = real['summary']['avg_empathy']

print(f"Simulated: {sim_empathy:.3f}")
print(f"Real: {real_empathy:.3f}")
print(f"Difference: {abs(sim_empathy - real_empathy):.3f}")
```

This ensures your experiment is methodologically sound! 🎓
