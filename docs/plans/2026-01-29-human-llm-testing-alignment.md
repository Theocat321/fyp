# Human-LLM Testing Alignment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Align human testing experience with LLM testing framework by adding scenario selection, rubric-aligned feedback ratings, and LAJ evaluation of human transcripts.

**Architecture:** Extend frontend enrollment to include scenario selection, enhance feedback modal with rubric questions (Task Success, Clarity, Empathy, Information Accuracy), update backend models to store scenario metadata and rubric ratings, create LAJ evaluation script for human transcripts.

**Tech Stack:** React/TypeScript (frontend), FastAPI/Python (backend), Supabase (storage), OpenAI API (LAJ evaluation)

---

## Task 1: Update Backend Models for Scenario Support

**Files:**
- Modify: `/Users/stagcto/fyp/server/app/models.py`

**Step 1: Add scenario fields to ParticipantInsert model**

```python
class ParticipantInsert(BaseModel):
    participant_id: str
    name: Optional[str] = None
    group: Optional[str] = None  # 'A' | 'B'
    session_id: Optional[str] = None
    scenario_id: Optional[str] = None  # NEW: Track which scenario human is testing
```

**Step 2: Add rubric rating fields to FeedbackInsert model**

```python
class FeedbackInsert(BaseModel):
    session_id: Optional[str] = None
    participant_id: Optional[str] = None
    participant_group: Optional[str] = None
    scenario_id: Optional[str] = None  # NEW
    rating_overall: Optional[int] = None
    rating_helpfulness: Optional[int] = None
    rating_friendliness: Optional[int] = None
    # NEW: Rubric-aligned ratings (1-5 scale)
    rating_task_success: Optional[int] = None
    rating_clarity: Optional[int] = None
    rating_empathy: Optional[int] = None
    rating_accuracy: Optional[int] = None
    resolved: Optional[bool] = None
    time_to_resolution: Optional[str] = None
    issues: Optional[list[str]] = []
    comments_positive: Optional[str] = None
    comments_negative: Optional[str] = None
    comments_other: Optional[str] = None
    would_use_again: Optional[str] = None
    recommend_nps: Optional[int] = None
    contact_ok: Optional[bool] = None
    contact_email: Optional[str] = None
    user_agent: Optional[str] = None
    page_url: Optional[str] = None
```

**Step 3: Verify changes**

Run: `cd /Users/stagcto/fyp/server && python -c "from app.models import ParticipantInsert, FeedbackInsert; print('Models updated successfully')"`
Expected: "Models updated successfully"

**Step 4: Commit**

```bash
git add server/app/models.py
git commit -m "feat: add scenario_id and rubric ratings to backend models"
```

---

## Task 2: Create Scenario API Endpoint

**Files:**
- Create: `/Users/stagcto/fyp/server/api/scenarios.py`

**Step 1: Create scenarios endpoint**

```python
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Scenario definitions matching LLM testing framework
SCENARIOS = [
    {
        "id": "scenario_001_esim_setup",
        "name": "eSIM Setup",
        "topic": "device",
        "description": "Get help setting up an eSIM on your device",
        "context": "You want to activate an eSIM but need guidance on compatibility and setup steps."
    },
    {
        "id": "scenario_002_roaming_activation",
        "name": "EU Roaming Activation",
        "topic": "roaming",
        "description": "Learn how to activate roaming for EU travel",
        "context": "You're traveling to the EU and need to understand roaming charges and activation."
    },
    {
        "id": "scenario_003_billing_dispute",
        "name": "Billing Dispute",
        "topic": "billing",
        "description": "Resolve an issue with your bill",
        "context": "You've noticed unexpected charges on your bill and want them explained or corrected."
    },
    {
        "id": "scenario_004_plan_upgrade",
        "name": "Plan Upgrade",
        "topic": "plans",
        "description": "Find the best plan for your needs",
        "context": "Your current plan isn't meeting your needs and you want to explore upgrade options."
    },
    {
        "id": "scenario_005_network_issue",
        "name": "Network Issue",
        "topic": "network",
        "description": "Fix connectivity or signal problems",
        "context": "You're experiencing poor signal or connection issues and need troubleshooting help."
    }
]

@router.get("/scenarios")
async def get_scenarios():
    """
    Return list of available test scenarios.

    GET /api/scenarios

    Returns:
        {
            "scenarios": [
                {
                    "id": "scenario_001_esim_setup",
                    "name": "eSIM Setup",
                    "topic": "device",
                    "description": "...",
                    "context": "..."
                },
                ...
            ]
        }
    """
    try:
        return JSONResponse(content={"scenarios": SCENARIOS}, status_code=200)
    except Exception as e:
        logger.exception("Failed to fetch scenarios")
        return JSONResponse(
            content={"error": "Failed to fetch scenarios"},
            status_code=500
        )
```

**Step 2: Register scenarios endpoint in main.py**

Modify: `/Users/stagcto/fyp/server/app/main.py`

Add import:
```python
from server.api import scenarios as scenarios_router
```

Add route registration (after other routers):
```python
app.include_router(scenarios_router.router, prefix="/api", tags=["scenarios"])
```

**Step 3: Test endpoint**

Run: `cd /Users/stagcto/fyp && curl http://localhost:8000/api/scenarios | jq`
Expected: JSON response with 5 scenarios

**Step 4: Commit**

```bash
git add server/api/scenarios.py server/app/main.py
git commit -m "feat: add scenarios API endpoint for human testing"
```

---

## Task 3: Update Supabase Schema

**Files:**
- Create: `/Users/stagcto/fyp/server/migrations/add_scenario_and_rubric_fields.sql`

**Step 1: Create migration SQL**

```sql
-- Add scenario_id to participants table
ALTER TABLE participants
ADD COLUMN IF NOT EXISTS scenario_id TEXT;

-- Add scenario_id and rubric ratings to support_feedback table
ALTER TABLE support_feedback
ADD COLUMN IF NOT EXISTS scenario_id TEXT,
ADD COLUMN IF NOT EXISTS rating_task_success INTEGER CHECK (rating_task_success >= 1 AND rating_task_success <= 5),
ADD COLUMN IF NOT EXISTS rating_clarity INTEGER CHECK (rating_clarity >= 1 AND rating_clarity <= 5),
ADD COLUMN IF NOT EXISTS rating_empathy INTEGER CHECK (rating_empathy >= 1 AND rating_empathy <= 5),
ADD COLUMN IF NOT EXISTS rating_accuracy INTEGER CHECK (rating_accuracy >= 1 AND rating_accuracy <= 5);

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_participants_scenario_id ON participants(scenario_id);
CREATE INDEX IF NOT EXISTS idx_support_feedback_scenario_id ON support_feedback(scenario_id);

-- Add comments for documentation
COMMENT ON COLUMN participants.scenario_id IS 'Scenario ID selected for testing session (e.g., scenario_001_esim_setup)';
COMMENT ON COLUMN support_feedback.scenario_id IS 'Scenario ID for this feedback session';
COMMENT ON COLUMN support_feedback.rating_task_success IS 'Rubric rating: Did assistant help accomplish goal? (1-5)';
COMMENT ON COLUMN support_feedback.rating_clarity IS 'Rubric rating: How clear were responses? (1-5)';
COMMENT ON COLUMN support_feedback.rating_empathy IS 'Rubric rating: How well did assistant acknowledge situation? (1-5)';
COMMENT ON COLUMN support_feedback.rating_accuracy IS 'Rubric rating: Information accuracy without unsupported claims? (1-5)';
```

**Step 2: Document migration instructions**

Create: `/Users/stagcto/fyp/server/migrations/README.md`

```markdown
# Database Migrations

## Applying Migrations

### Via Supabase Dashboard (Recommended)

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy the contents of the migration file
4. Paste and execute

### Via psql (Alternative)

```bash
psql "postgresql://[username]:[password]@[host]:5432/[database]?sslmode=require" \
  -f add_scenario_and_rubric_fields.sql
```

## Migration: add_scenario_and_rubric_fields.sql

**Date:** 2026-01-29
**Purpose:** Add scenario tracking and rubric ratings for human-LLM testing alignment

**Changes:**
- Add `scenario_id` to `participants` table
- Add `scenario_id` and rubric rating columns to `support_feedback` table
- Add indexes for query performance
```

**Step 3: Commit**

```bash
git add server/migrations/
git commit -m "feat: add database migration for scenario and rubric fields"
```

**Step 4: Apply migration (manual step)**

Note: Run this SQL in Supabase dashboard after review

---

## Task 4: Update Frontend - Add Scenario Selection

**Files:**
- Modify: `/Users/stagcto/fyp/web/components/ChatWindow.tsx`

**Step 1: Add scenario state and API call**

Add after line 27 (after participant state):

```typescript
  // Scenario selection
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>("");
  const [scenarioContext, setScenarioContext] = useState<string>("");
```

Add after line 107 (in useEffect for loading participant):

```typescript
  // Load scenarios
  useEffect(() => {
    (async () => {
      try {
        const resp = await fetch("/api/scenarios");
        const data = await resp.json();
        setScenarios(data.scenarios || []);
      } catch (e) {
        console.error("Failed to load scenarios:", e);
      }
    })();
  }, []);
```

**Step 2: Update enrollment form to include scenario selection**

Replace the enrollment form (lines 382-406) with:

```tsx
  if (!started) {
    return (
      <div className="prechat-shell">
        <div className="prechat-card">
          <h2>Study Enrollment</h2>
          <p className="muted">Enter your details to start the research chat.</p>
          <form onSubmit={onStartStudy} className="prechat-form">
            <div className="field-row">
              <label htmlFor="participant-name" className="label">Name</label>
              <input
                id="participant-name"
                className="text-input"
                placeholder="Your name"
                value={participantName}
                onChange={(e) => setParticipantName(e.target.value)}
              />
            </div>
            <div className="field-row">
              <label htmlFor="participant-group" className="label">Group</label>
              <select
                id="participant-group"
                className="select"
                value={participantGroup}
                onChange={(e) => setParticipantGroup(e.target.value as any)}
              >
                <option value="">Select group…</option>
                <option value="A">A</option>
                <option value="B">B</option>
              </select>
            </div>
            <div className="field-row">
              <label htmlFor="scenario" className="label">Scenario (Optional)</label>
              <select
                id="scenario"
                className="select"
                value={selectedScenario}
                onChange={(e) => {
                  const scenarioId = e.target.value;
                  setSelectedScenario(scenarioId);
                  const scenario = scenarios.find(s => s.id === scenarioId);
                  setScenarioContext(scenario ? scenario.context : "");
                }}
              >
                <option value="">None (free conversation)</option>
                {scenarios.map(s => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
            {scenarioContext && (
              <div className="scenario-context">
                <strong>Scenario Context:</strong>
                <p className="muted">{scenarioContext}</p>
              </div>
            )}
            <button
              className="send-btn"
              type="submit"
              disabled={!participantName.trim() || !(participantGroup === "A" || participantGroup === "B")}
            >
              Start Chat
            </button>
          </form>
          <p className="consent-note">
            By starting, you consent to your inputs being used for research. Do not share sensitive information.
          </p>
        </div>
      </div>
    );
  }
```

**Step 3: Update onStartStudy to persist scenario**

Modify `onStartStudy` function (line 129) to include scenario:

```typescript
  async function onStartStudy(e: React.FormEvent) {
    e.preventDefault();
    if (!participantName.trim() || !(participantGroup === "A" || participantGroup === "B")) return;
    try {
      localStorage.setItem("vc_participant_name", participantName.trim());
      localStorage.setItem("vc_participant_group", participantGroup);
      if (selectedScenario) {
        localStorage.setItem("vc_scenario_id", selectedScenario);
      }
    } catch {}
    const pid = ensureParticipantId();
    const sid = ensureSessionId();
    // Log enrollment submit
    try {
      await logEvent({
        session_id: sid,
        participant_id: pid,
        participant_group: participantGroup,
        event: "submit",
        component: "start_chat_form",
        label: "start_chat",
        value: participantGroup,
        client_ts: Date.now(),
        page_url: typeof window !== "undefined" ? window.location.href : undefined,
        meta: { scenario_id: selectedScenario || null },
      });
    } catch {}
    // Participant upsert via Python backend
    try {
      await fetch("/api/participants", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          participant_id: pid,
          name: participantName.trim(),
          group: participantGroup,
          session_id: sid,
          scenario_id: selectedScenario || null,
        }),
      });
    } catch {}
    setStarted(true);
  }
```

**Step 4: Load scenario from localStorage**

Update the participant loading useEffect (line 93) to include scenario:

```typescript
  // Load participant from localStorage
  useEffect(() => {
    try {
      const name = localStorage.getItem("vc_participant_name") || "";
      const group = (localStorage.getItem("vc_participant_group") || "") as "A" | "B" | "";
      const pid = localStorage.getItem("vc_participant_id") || undefined;
      const sid = localStorage.getItem("vc_session_id") || undefined;
      const scenario = localStorage.getItem("vc_scenario_id") || "";
      if (name && (group === "A" || group === "B")) {
        setParticipantName(name);
        setParticipantGroup(group);
        if (pid) setParticipantId(pid);
        if (sid) setSessionId(sid);
        if (scenario) setSelectedScenario(scenario);
        setStarted(true);
      }
    } catch {}
  }, []);
```

**Step 5: Add CSS for scenario context**

Create: `/Users/stagcto/fyp/web/app/globals.css` (append to existing file)

```css
.scenario-context {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 3px solid #0066cc;
}

.scenario-context strong {
  display: block;
  margin-bottom: 0.5rem;
  color: #333;
}

.scenario-context p {
  margin: 0;
  font-size: 0.9rem;
}
```

**Step 6: Test scenario selection**

Run: `cd /Users/stagcto/fyp/web && npm run dev`
Navigate to: http://localhost:3000
Expected: Scenario dropdown appears in enrollment form

**Step 7: Commit**

```bash
git add web/components/ChatWindow.tsx web/app/globals.css
git commit -m "feat: add scenario selection to enrollment form"
```

---

## Task 5: Update Feedback Modal with Rubric Ratings

**Files:**
- Modify: `/Users/stagcto/fyp/web/components/ChatWindow.tsx`

**Step 1: Add rubric rating fields to form state**

Update form state (line 35) to include:

```typescript
  const [form, setForm] = useState({
    rating_overall: 0,
    rating_helpfulness: 0,
    rating_friendliness: 0,
    // NEW: Rubric-aligned ratings
    rating_task_success: 0,
    rating_clarity: 0,
    rating_empathy: 0,
    rating_accuracy: 0,
    resolved: "",
    time_to_resolution: "",
    issues: [] as string[],
    comments_positive: "",
    comments_negative: "",
    comments_other: "",
    would_use_again: "",
    recommend_nps: 0,
    contact_ok: false,
    contact_email: "",
  });
```

**Step 2: Add rubric rating questions to feedback form**

Insert after line 635 (after friendliness rating, before resolved question):

```tsx
                  </div>

                  <div className="rubric-section">
                    <h4 className="rubric-heading">Help us improve: Rate the conversation quality</h4>
                    <p className="muted">These ratings help us understand how well the assistant performed.</p>

                    <div className="field-row">
                      <label className="label">
                        Task Success: Did the assistant help you accomplish your goal?
                      </label>
                      <div className="rating-stars" aria-label="Task success rating">
                        {[1,2,3,4,5].map((n) => (
                          <button
                            key={n}
                            type="button"
                            className={"star" + (form.rating_task_success >= n ? " filled" : "")}
                            onClick={() => setForm({ ...form, rating_task_success: n })}
                            aria-label={`${n} star${n>1?"s":""}`}
                          >
                            ★
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="field-row">
                      <label className="label">
                        Clarity: How clear and understandable were the responses?
                      </label>
                      <div className="rating-stars" aria-label="Clarity rating">
                        {[1,2,3,4,5].map((n) => (
                          <button
                            key={n}
                            type="button"
                            className={"star" + (form.rating_clarity >= n ? " filled" : "")}
                            onClick={() => setForm({ ...form, rating_clarity: n })}
                            aria-label={`${n} star${n>1?"s":""}`}
                          >
                            ★
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="field-row">
                      <label className="label">
                        Empathy: How well did the assistant acknowledge your situation/feelings?
                      </label>
                      <div className="rating-stars" aria-label="Empathy rating">
                        {[1,2,3,4,5].map((n) => (
                          <button
                            key={n}
                            type="button"
                            className={"star" + (form.rating_empathy >= n ? " filled" : "")}
                            onClick={() => setForm({ ...form, rating_empathy: n })}
                            aria-label={`${n} star${n>1?"s":""}`}
                          >
                            ★
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="field-row">
                      <label className="label">
                        Information Accuracy: Did the assistant provide accurate information without making unsupported claims?
                      </label>
                      <div className="rating-stars" aria-label="Accuracy rating">
                        {[1,2,3,4,5].map((n) => (
                          <button
                            key={n}
                            type="button"
                            className={"star" + (form.rating_accuracy >= n ? " filled" : "")}
                            onClick={() => setForm({ ...form, rating_accuracy: n })}
                            aria-label={`${n} star${n>1?"s":""}`}
                          >
                            ★
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="grid-2">
                    <div className="field-row">
                      <label className="label">Was your issue resolved?</label>
```

**Step 3: Update feedback submission payload**

Update feedback submission (line 556) to include rubric ratings and scenario:

```typescript
                    const payload: any = {
                      session_id: sid,
                      participant_id: pid,
                      participant_group: participantGroup || null,
                      scenario_id: selectedScenario || null,
                      rating_overall: form.rating_overall || null,
                      rating_helpfulness: form.rating_helpfulness || null,
                      rating_friendliness: form.rating_friendliness || null,
                      rating_task_success: form.rating_task_success || null,
                      rating_clarity: form.rating_clarity || null,
                      rating_empathy: form.rating_empathy || null,
                      rating_accuracy: form.rating_accuracy || null,
                      resolved: form.resolved === "yes" ? true : form.resolved === "no" ? false : null,
                      time_to_resolution: form.time_to_resolution || null,
                      issues: form.issues,
                      comments_positive: form.comments_positive || null,
                      comments_negative: form.comments_negative || null,
                      comments_other: form.comments_other || null,
                      would_use_again: form.would_use_again || null,
                      recommend_nps: form.recommend_nps || null,
                      contact_ok: form.contact_ok,
                      contact_email: form.contact_email || null,
                      user_agent: typeof navigator !== "undefined" ? navigator.userAgent : null,
                      page_url: typeof window !== "undefined" ? window.location.href : null,
                    };
```

**Step 4: Add CSS for rubric section**

Append to `/Users/stagcto/fyp/web/app/globals.css`:

```css
.rubric-section {
  margin: 1.5rem 0;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.rubric-heading {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  color: #333;
}

.rubric-section .field-row {
  margin-bottom: 1rem;
}

.rubric-section .field-row:last-child {
  margin-bottom: 0;
}

.rubric-section .label {
  font-size: 0.9rem;
  line-height: 1.4;
}
```

**Step 5: Test feedback form**

Run: `cd /Users/stagcto/fyp/web && npm run dev`
Navigate to chat, click Finish button
Expected: Feedback modal shows 4 new rubric rating questions

**Step 6: Commit**

```bash
git add web/components/ChatWindow.tsx web/app/globals.css
git commit -m "feat: add rubric-aligned ratings to feedback modal"
```

---

## Task 6: Create LAJ Evaluation Script for Human Transcripts

**Files:**
- Create: `/Users/stagcto/fyp/llm-testing/evaluate_human_transcripts.py`

**Step 1: Create evaluation script**

```python
#!/usr/bin/env python3
"""
Evaluate human conversation transcripts using LLM-as-Judge.

This script fetches human conversation transcripts from Supabase,
runs the same LLM-as-Judge evaluation used for simulated conversations,
and compares human self-ratings with LAJ ratings.

Usage:
    python evaluate_human_transcripts.py --session-id abc123
    python evaluate_human_transcripts.py --all --output results.json
    python evaluate_human_transcripts.py --participant-group A
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from openai import OpenAI
import requests

# Import from llm-testing framework
sys.path.insert(0, str(Path(__file__).parent))
from src.evaluator.llm_judge import LLMJudge
from src.evaluator.heuristics import HeuristicEvaluator
from src.artifacts.models import ConversationTurn
from src.config.settings import load_config

logger = logging.getLogger(__name__)


class HumanTranscriptEvaluator:
    """Evaluates human conversation transcripts using LAJ."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.openai_client = OpenAI(api_key=config['openai_api_key'])
        self.llm_judge = LLMJudge(
            self.openai_client,
            config['judge_model'],
            config['rubric']
        )
        self.heuristic_evaluator = HeuristicEvaluator()

        # Supabase connection
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set"
            )

    def fetch_messages(self, session_id: str) -> List[Dict]:
        """Fetch messages for a session from Supabase."""
        url = f"{self.supabase_url}/rest/v1/messages"
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
        }
        params = {
            "session_id": f"eq.{session_id}",
            "order": "created_at.asc"
        }

        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def fetch_feedback(self, session_id: str) -> Optional[Dict]:
        """Fetch feedback for a session from Supabase."""
        url = f"{self.supabase_url}/rest/v1/support_feedback"
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
        }
        params = {
            "session_id": f"eq.{session_id}",
            "limit": "1"
        }

        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json()
        return results[0] if results else None

    def fetch_participant(self, session_id: str) -> Optional[Dict]:
        """Fetch participant info for a session from Supabase."""
        url = f"{self.supabase_url}/rest/v1/participants"
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
        }
        params = {
            "session_id": f"eq.{session_id}",
            "limit": "1"
        }

        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json()
        return results[0] if results else None

    def fetch_all_sessions(
        self,
        participant_group: Optional[str] = None
    ) -> List[str]:
        """Fetch all session IDs, optionally filtered by group."""
        url = f"{self.supabase_url}/rest/v1/messages"
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
        }
        params = {
            "select": "session_id"
        }

        if participant_group:
            params["participant_group"] = f"eq.{participant_group}"

        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()

        # Extract unique session IDs
        session_ids = list(set(msg["session_id"] for msg in resp.json()))
        return session_ids

    def evaluate_session(self, session_id: str) -> Dict[str, Any]:
        """
        Evaluate a single human conversation session.

        Returns:
            {
                'session_id': str,
                'participant': {...},
                'transcript': [...],
                'human_feedback': {...},
                'laj_evaluation': {...},
                'heuristic_evaluation': {...},
                'comparison': {...}
            }
        """
        logger.info(f"Evaluating session: {session_id}")

        # Fetch data
        messages = self.fetch_messages(session_id)
        feedback = self.fetch_feedback(session_id)
        participant = self.fetch_participant(session_id)

        if not messages:
            logger.warning(f"No messages found for session {session_id}")
            return None

        # Convert to transcript format
        transcript = [
            ConversationTurn(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["created_at"]
            )
            for msg in messages
        ]

        # Create minimal persona and scenario for LAJ context
        # (Since humans chose their own goals, we use generic context)
        from src.persona.models import (
            Persona, Demographics, Personality, Goals,
            Constraints, ConversationParameters
        )
        from src.scenario.models import (
            Scenario, SuccessCriteria, Context
        )

        # Generic persona representing human tester
        generic_persona = Persona(
            id="human_tester",
            name=participant.get("name", "Anonymous") if participant else "Anonymous",
            version="1.0",
            demographics=Demographics(
                age=30,
                location="Unknown",
                occupation="Research Participant",
                tech_literacy="moderate"
            ),
            personality=Personality(
                tone_style="natural",
                communication_style="conversational",
                patience_level="moderate",
                emotional_state="neutral"
            ),
            behavioral_traits=["authentic_human_interaction"],
            goals=Goals(primary="Test the chatbot system"),
            constraints=Constraints(),
            seed_utterance=messages[0]["content"] if messages else "",
            conversation_parameters=ConversationParameters()
        )

        # Get scenario if available
        scenario_id = participant.get("scenario_id") if participant else None
        if scenario_id:
            # Load actual scenario
            from src.scenario.loader import ScenarioLoader
            loader = ScenarioLoader(Path(__file__).parent / "data" / "scenarios")
            try:
                scenario = loader.load(scenario_id)
            except:
                scenario = self._create_generic_scenario()
        else:
            scenario = self._create_generic_scenario()

        # Run LAJ evaluation
        variant = participant.get("group", "Unknown") if participant else "Unknown"
        laj_eval = self.llm_judge.evaluate_conversation(
            generic_persona,
            scenario,
            [(t.role, t.content, 0) for t in transcript],
            variant
        )

        # Run heuristic evaluation
        heuristic_eval = self.heuristic_evaluator.evaluate(transcript)

        # Compare human self-ratings with LAJ ratings
        comparison = None
        if feedback:
            comparison = self._compare_ratings(feedback, laj_eval)

        return {
            'session_id': session_id,
            'participant': participant,
            'transcript': [t.model_dump() for t in transcript],
            'human_feedback': feedback,
            'laj_evaluation': laj_eval,
            'heuristic_evaluation': heuristic_eval,
            'comparison': comparison,
            'evaluated_at': datetime.utcnow().isoformat()
        }

    def _create_generic_scenario(self) -> Any:
        """Create generic scenario for unstructured conversations."""
        from src.scenario.models import (
            Scenario, SuccessCriteria, Context, HappyPathStep
        )

        return Scenario(
            id="scenario_000_generic",
            name="Generic Support Request",
            version="1.0",
            topic="support",
            description="General customer support inquiry",
            context=Context(),
            happy_path_steps=[
                HappyPathStep(
                    step_number=1,
                    description="Understand user need",
                    expected_info=["User goal identified"]
                )
            ],
            edge_cases=[],
            success_criteria=SuccessCriteria(
                must_provide=["Helpful response"],
                must_avoid=["Incorrect information"],
                escalation_conditions=[]
            ),
            typical_questions=[],
            knowledge_requirements=[]
        )

    def _compare_ratings(
        self,
        feedback: Dict[str, Any],
        laj_eval: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare human self-ratings with LAJ ratings.

        Returns:
            {
                'task_success': {'human': 4, 'laj': 0.85, 'diff': 0.05},
                'clarity': {...},
                'empathy': {...},
                'accuracy': {...},
                'overall_alignment': 0.92
            }
        """
        # Convert human 1-5 ratings to 0-1 scale for comparison
        def normalize(rating_1_5: Optional[int]) -> Optional[float]:
            if rating_1_5 is None:
                return None
            return (rating_1_5 - 1) / 4.0  # 1->0.0, 5->1.0

        human_task = normalize(feedback.get('rating_task_success'))
        human_clarity = normalize(feedback.get('rating_clarity'))
        human_empathy = normalize(feedback.get('rating_empathy'))
        human_accuracy = normalize(feedback.get('rating_accuracy'))

        laj_scores = laj_eval['scores']

        comparison = {}

        if human_task is not None:
            comparison['task_success'] = {
                'human': feedback['rating_task_success'],
                'human_normalized': human_task,
                'laj': laj_scores['task_success'],
                'diff': abs(human_task - laj_scores['task_success'])
            }

        if human_clarity is not None:
            comparison['clarity'] = {
                'human': feedback['rating_clarity'],
                'human_normalized': human_clarity,
                'laj': laj_scores['clarity'],
                'diff': abs(human_clarity - laj_scores['clarity'])
            }

        if human_empathy is not None:
            comparison['empathy'] = {
                'human': feedback['rating_empathy'],
                'human_normalized': human_empathy,
                'laj': laj_scores['empathy'],
                'diff': abs(human_empathy - laj_scores['empathy'])
            }

        if human_accuracy is not None:
            comparison['accuracy'] = {
                'human': feedback['rating_accuracy'],
                'human_normalized': human_accuracy,
                'laj': laj_scores['policy_compliance'],  # Map to policy compliance
                'diff': abs(human_accuracy - laj_scores['policy_compliance'])
            }

        # Calculate overall alignment (lower is better, 0.0 = perfect agreement)
        diffs = [c['diff'] for c in comparison.values()]
        comparison['overall_alignment'] = 1.0 - (sum(diffs) / len(diffs)) if diffs else None

        return comparison


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Evaluate human conversation transcripts using LLM-as-Judge'
    )

    parser.add_argument(
        '--session-id',
        type=str,
        help='Evaluate a specific session ID'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Evaluate all sessions in database'
    )

    parser.add_argument(
        '--participant-group',
        type=str,
        choices=['A', 'B'],
        help='Filter by participant group (A or B)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='human_evaluations.json',
        help='Output file path (default: human_evaluations.json)'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('human_evaluation.log')
        ]
    )

    logger.info("=" * 60)
    logger.info("Human Transcript LAJ Evaluation")
    logger.info("=" * 60)

    try:
        # Load configuration
        load_dotenv()
        config = load_config()

        evaluator = HumanTranscriptEvaluator(config)

        # Determine which sessions to evaluate
        if args.session_id:
            session_ids = [args.session_id]
        elif args.all:
            session_ids = evaluator.fetch_all_sessions(args.participant_group)
            logger.info(f"Found {len(session_ids)} sessions to evaluate")
        else:
            logger.error("Must specify --session-id or --all")
            sys.exit(1)

        # Evaluate sessions
        results = []
        for sid in session_ids:
            try:
                result = evaluator.evaluate_session(sid)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Failed to evaluate session {sid}: {e}")
                continue

        # Write results
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump({
                'evaluated_at': datetime.utcnow().isoformat(),
                'total_sessions': len(results),
                'participant_group_filter': args.participant_group,
                'evaluations': results
            }, f, indent=2)

        logger.info(f"Evaluation complete. Results written to {output_path}")
        logger.info(f"Successfully evaluated {len(results)} sessions")

        # Print summary
        if results:
            avg_alignment = sum(
                r['comparison']['overall_alignment']
                for r in results
                if r['comparison'] and r['comparison']['overall_alignment'] is not None
            ) / len([r for r in results if r['comparison']])

            logger.info("=" * 60)
            logger.info("SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Average human-LAJ alignment: {avg_alignment:.2%}")
            logger.info("=" * 60)

    except Exception as e:
        logger.exception(f"Evaluation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
```

**Step 2: Make script executable**

Run: `chmod +x /Users/stagcto/fyp/llm-testing/evaluate_human_transcripts.py`

**Step 3: Update requirements.txt**

Append to `/Users/stagcto/fyp/llm-testing/requirements.txt`:

```txt
requests>=2.32.0
```

**Step 4: Test script (dry run)**

Run: `cd /Users/stagcto/fyp/llm-testing && python evaluate_human_transcripts.py --help`
Expected: Help message displays

**Step 5: Commit**

```bash
git add llm-testing/evaluate_human_transcripts.py llm-testing/requirements.txt
git commit -m "feat: add LAJ evaluation script for human transcripts"
```

---

## Task 7: Create Comparison Report Generator

**Files:**
- Create: `/Users/stagcto/fyp/llm-testing/generate_comparison_report.py`

**Step 1: Create report generator script**

```python
#!/usr/bin/env python3
"""
Generate comparison report between LLM-simulated and human testing results.

Usage:
    python generate_comparison_report.py \
        --llm-results outputs/exp_20260129_*.json \
        --human-results human_evaluations.json \
        --output comparison_report.html
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


def load_llm_results(pattern: str) -> List[Dict]:
    """Load LLM experiment results."""
    results = []
    for path in Path().glob(pattern):
        with open(path, 'r') as f:
            results.append(json.load(f))
    return results


def load_human_results(path: str) -> Dict:
    """Load human evaluation results."""
    with open(path, 'r') as f:
        return json.load(f)


def generate_html_report(
    llm_results: List[Dict],
    human_results: Dict,
    output_path: str
):
    """Generate HTML comparison report."""

    # Calculate aggregate statistics
    llm_stats = calculate_llm_stats(llm_results)
    human_stats = calculate_human_stats(human_results)

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VodaCare Testing Comparison Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 8px;
            margin-bottom: 2rem;
        }}
        .header h1 {{
            margin: 0 0 0.5rem 0;
        }}
        .header p {{
            margin: 0;
            opacity: 0.9;
        }}
        .card {{
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .card h2 {{
            margin: 0 0 1rem 0;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 0.5rem;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        .stat-box {{
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }}
        .stat-label {{
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 0.25rem;
        }}
        .stat-value {{
            font-size: 1.75rem;
            font-weight: 600;
            color: #333;
        }}
        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        .comparison-table th {{
            background: #f8f9fa;
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #dee2e6;
        }}
        .comparison-table td {{
            padding: 0.75rem;
            border-bottom: 1px solid #dee2e6;
        }}
        .comparison-table tr:hover {{
            background: #f8f9fa;
        }}
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        .badge-a {{
            background: #d4edda;
            color: #155724;
        }}
        .badge-b {{
            background: #d1ecf1;
            color: #0c5460;
        }}
        .highlight {{
            background: #fff3cd;
            padding: 1rem;
            border-left: 4px solid #ffc107;
            border-radius: 4px;
            margin: 1rem 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 VodaCare Testing Comparison Report</h1>
        <p>LLM-Simulated vs Human Testing Results</p>
        <p>Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
    </div>

    <div class="card">
        <h2>📊 Overall Statistics</h2>
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-label">LLM Test Runs</div>
                <div class="stat-value">{llm_stats['total_runs']}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Human Test Sessions</div>
                <div class="stat-value">{human_stats['total_sessions']}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">LLM Avg Score</div>
                <div class="stat-value">{llm_stats['avg_overall']:.2f}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Human-LAJ Alignment</div>
                <div class="stat-value">{human_stats['avg_alignment']:.0%}</div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>🎯 Rubric Scores Comparison</h2>
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>Dimension</th>
                    <th>LLM Simulated (LAJ)</th>
                    <th>Human Self-Rating</th>
                    <th>Human (LAJ)</th>
                    <th>Variance</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Task Success</td>
                    <td>{llm_stats['avg_task_success']:.2f}</td>
                    <td>{human_stats['avg_self_task_success']:.2f}</td>
                    <td>{human_stats['avg_laj_task_success']:.2f}</td>
                    <td>{abs(llm_stats['avg_task_success'] - human_stats['avg_laj_task_success']):.2f}</td>
                </tr>
                <tr>
                    <td>Clarity</td>
                    <td>{llm_stats['avg_clarity']:.2f}</td>
                    <td>{human_stats['avg_self_clarity']:.2f}</td>
                    <td>{human_stats['avg_laj_clarity']:.2f}</td>
                    <td>{abs(llm_stats['avg_clarity'] - human_stats['avg_laj_clarity']):.2f}</td>
                </tr>
                <tr>
                    <td>Empathy</td>
                    <td>{llm_stats['avg_empathy']:.2f}</td>
                    <td>{human_stats['avg_self_empathy']:.2f}</td>
                    <td>{human_stats['avg_laj_empathy']:.2f}</td>
                    <td>{abs(llm_stats['avg_empathy'] - human_stats['avg_laj_empathy']):.2f}</td>
                </tr>
                <tr>
                    <td>Accuracy/Policy</td>
                    <td>{llm_stats['avg_policy']:.2f}</td>
                    <td>{human_stats['avg_self_accuracy']:.2f}</td>
                    <td>{human_stats['avg_laj_accuracy']:.2f}</td>
                    <td>{abs(llm_stats['avg_policy'] - human_stats['avg_laj_accuracy']):.2f}</td>
                </tr>
            </tbody>
        </table>

        <div class="highlight">
            <strong>Key Finding:</strong> Human self-ratings tend to be
            {("higher" if human_stats['self_vs_laj_bias'] > 0 else "lower")} than LAJ ratings
            by an average of {abs(human_stats['self_vs_laj_bias']):.2f} points.
        </div>
    </div>

    <div class="card">
        <h2>🔬 Variant A vs B Performance</h2>
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Variant A (Kindness)</th>
                    <th>Variant B (Confirmation)</th>
                    <th>Winner</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Overall Score (LLM)</td>
                    <td>{llm_stats['variant_a']['avg_overall']:.2f}</td>
                    <td>{llm_stats['variant_b']['avg_overall']:.2f}</td>
                    <td><span class="badge badge-{('a' if llm_stats['variant_a']['avg_overall'] > llm_stats['variant_b']['avg_overall'] else 'b')}">
                        Variant {('A' if llm_stats['variant_a']['avg_overall'] > llm_stats['variant_b']['avg_overall'] else 'B')}
                    </span></td>
                </tr>
                <tr>
                    <td>Empathy Score (LLM)</td>
                    <td>{llm_stats['variant_a']['avg_empathy']:.2f}</td>
                    <td>{llm_stats['variant_b']['avg_empathy']:.2f}</td>
                    <td><span class="badge badge-{('a' if llm_stats['variant_a']['avg_empathy'] > llm_stats['variant_b']['avg_empathy'] else 'b')}">
                        Variant {('A' if llm_stats['variant_a']['avg_empathy'] > llm_stats['variant_b']['avg_empathy'] else 'B')}
                    </span></td>
                </tr>
                <tr>
                    <td>Clarity Score (LLM)</td>
                    <td>{llm_stats['variant_a']['avg_clarity']:.2f}</td>
                    <td>{llm_stats['variant_b']['avg_clarity']:.2f}</td>
                    <td><span class="badge badge-{('a' if llm_stats['variant_a']['avg_clarity'] > llm_stats['variant_b']['avg_clarity'] else 'b')}">
                        Variant {('A' if llm_stats['variant_a']['avg_clarity'] > llm_stats['variant_b']['avg_clarity'] else 'B')}
                    </span></td>
                </tr>
                <tr>
                    <td>Human Satisfaction (Self)</td>
                    <td>{human_stats['variant_a']['avg_satisfaction']:.2f}</td>
                    <td>{human_stats['variant_b']['avg_satisfaction']:.2f}</td>
                    <td><span class="badge badge-{('a' if human_stats['variant_a']['avg_satisfaction'] > human_stats['variant_b']['avg_satisfaction'] else 'b')}">
                        Variant {('A' if human_stats['variant_a']['avg_satisfaction'] > human_stats['variant_b']['avg_satisfaction'] else 'B')}
                    </span></td>
                </tr>
            </tbody>
        </table>
    </div>

    <div class="card">
        <h2>📋 Methodology Notes</h2>
        <ul>
            <li><strong>LLM Testing:</strong> {llm_stats['total_runs']} conversations across 20 personas and 5 scenarios, evaluated by LLM-as-Judge using consistent rubric</li>
            <li><strong>Human Testing:</strong> {human_stats['total_sessions']} real user sessions with self-ratings and LAJ evaluation for comparison</li>
            <li><strong>Rubric Alignment:</strong> Both human and LLM testing use identical evaluation criteria (Task Success, Clarity, Empathy, Accuracy)</li>
            <li><strong>Self-Rating Bias:</strong> Human self-ratings compared against LAJ evaluation to measure rating variance</li>
        </ul>
    </div>
</body>
</html>
"""

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"Report generated: {output_path}")


def calculate_llm_stats(results: List[Dict]) -> Dict[str, Any]:
    """Calculate aggregate statistics from LLM results."""
    all_runs = []
    for exp in results:
        all_runs.extend(exp.get('conversation_runs', []))

    if not all_runs:
        return {
            'total_runs': 0,
            'avg_overall': 0,
            'avg_task_success': 0,
            'avg_clarity': 0,
            'avg_empathy': 0,
            'avg_policy': 0,
            'variant_a': {'avg_overall': 0, 'avg_empathy': 0, 'avg_clarity': 0},
            'variant_b': {'avg_overall': 0, 'avg_empathy': 0, 'avg_clarity': 0}
        }

    # Overall stats
    scores = [r['llm_evaluation']['scores'] for r in all_runs]

    # Variant-specific stats
    variant_a_runs = [r for r in all_runs if r['variant'] == 'A']
    variant_b_runs = [r for r in all_runs if r['variant'] == 'B']

    return {
        'total_runs': len(all_runs),
        'avg_overall': sum(s['overall'] for s in scores) / len(scores),
        'avg_task_success': sum(s['task_success'] for s in scores) / len(scores),
        'avg_clarity': sum(s['clarity'] for s in scores) / len(scores),
        'avg_empathy': sum(s['empathy'] for s in scores) / len(scores),
        'avg_policy': sum(s['policy_compliance'] for s in scores) / len(scores),
        'variant_a': {
            'avg_overall': sum(r['llm_evaluation']['scores']['overall'] for r in variant_a_runs) / len(variant_a_runs) if variant_a_runs else 0,
            'avg_empathy': sum(r['llm_evaluation']['scores']['empathy'] for r in variant_a_runs) / len(variant_a_runs) if variant_a_runs else 0,
            'avg_clarity': sum(r['llm_evaluation']['scores']['clarity'] for r in variant_a_runs) / len(variant_a_runs) if variant_a_runs else 0,
        },
        'variant_b': {
            'avg_overall': sum(r['llm_evaluation']['scores']['overall'] for r in variant_b_runs) / len(variant_b_runs) if variant_b_runs else 0,
            'avg_empathy': sum(r['llm_evaluation']['scores']['empathy'] for r in variant_b_runs) / len(variant_b_runs) if variant_b_runs else 0,
            'avg_clarity': sum(r['llm_evaluation']['scores']['clarity'] for r in variant_b_runs) / len(variant_b_runs) if variant_b_runs else 0,
        }
    }


def calculate_human_stats(results: Dict) -> Dict[str, Any]:
    """Calculate aggregate statistics from human results."""
    evals = results.get('evaluations', [])

    if not evals:
        return {
            'total_sessions': 0,
            'avg_alignment': 0,
            'avg_self_task_success': 0,
            'avg_self_clarity': 0,
            'avg_self_empathy': 0,
            'avg_self_accuracy': 0,
            'avg_laj_task_success': 0,
            'avg_laj_clarity': 0,
            'avg_laj_empathy': 0,
            'avg_laj_accuracy': 0,
            'self_vs_laj_bias': 0,
            'variant_a': {'avg_satisfaction': 0},
            'variant_b': {'avg_satisfaction': 0}
        }

    # Filter evals with comparison data
    with_comparison = [e for e in evals if e.get('comparison')]

    # Self-ratings (normalized to 0-1)
    self_ratings = []
    for e in evals:
        fb = e.get('human_feedback', {})
        if fb:
            self_ratings.append({
                'task': (fb.get('rating_task_success', 3) - 1) / 4,
                'clarity': (fb.get('rating_clarity', 3) - 1) / 4,
                'empathy': (fb.get('rating_empathy', 3) - 1) / 4,
                'accuracy': (fb.get('rating_accuracy', 3) - 1) / 4,
            })

    # LAJ ratings
    laj_ratings = [e['laj_evaluation']['scores'] for e in evals]

    # Calculate bias (self vs LAJ)
    biases = []
    for e in with_comparison:
        comp = e['comparison']
        for dim in ['task_success', 'clarity', 'empathy', 'accuracy']:
            if dim in comp:
                biases.append(comp[dim]['human_normalized'] - comp[dim]['laj'])

    # Variant-specific
    variant_a = [e for e in evals if e.get('participant', {}).get('group') == 'A']
    variant_b = [e for e in evals if e.get('participant', {}).get('group') == 'B']

    return {
        'total_sessions': len(evals),
        'avg_alignment': sum(e['comparison']['overall_alignment'] for e in with_comparison) / len(with_comparison) if with_comparison else 0,
        'avg_self_task_success': sum(r['task'] for r in self_ratings) / len(self_ratings) if self_ratings else 0,
        'avg_self_clarity': sum(r['clarity'] for r in self_ratings) / len(self_ratings) if self_ratings else 0,
        'avg_self_empathy': sum(r['empathy'] for r in self_ratings) / len(self_ratings) if self_ratings else 0,
        'avg_self_accuracy': sum(r['accuracy'] for r in self_ratings) / len(self_ratings) if self_ratings else 0,
        'avg_laj_task_success': sum(s['task_success'] for s in laj_ratings) / len(laj_ratings),
        'avg_laj_clarity': sum(s['clarity'] for s in laj_ratings) / len(laj_ratings),
        'avg_laj_empathy': sum(s['empathy'] for s in laj_ratings) / len(laj_ratings),
        'avg_laj_accuracy': sum(s['policy_compliance'] for s in laj_ratings) / len(laj_ratings),
        'self_vs_laj_bias': sum(biases) / len(biases) if biases else 0,
        'variant_a': {
            'avg_satisfaction': sum(
                e['human_feedback'].get('rating_overall', 3)
                for e in variant_a
                if e.get('human_feedback')
            ) / len(variant_a) if variant_a else 0
        },
        'variant_b': {
            'avg_satisfaction': sum(
                e['human_feedback'].get('rating_overall', 3)
                for e in variant_b
                if e.get('human_feedback')
            ) / len(variant_b) if variant_b else 0
        }
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate comparison report between LLM and human testing'
    )

    parser.add_argument(
        '--llm-results',
        type=str,
        required=True,
        help='Glob pattern for LLM experiment results (e.g., "outputs/exp_*.json")'
    )

    parser.add_argument(
        '--human-results',
        type=str,
        required=True,
        help='Path to human evaluation results JSON'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='comparison_report.html',
        help='Output HTML file path (default: comparison_report.html)'
    )

    args = parser.parse_args()

    try:
        # Load results
        llm_results = load_llm_results(args.llm_results)
        human_results = load_human_results(args.human_results)

        print(f"Loaded {len(llm_results)} LLM experiment files")
        print(f"Loaded {human_results.get('total_sessions', 0)} human sessions")

        # Generate report
        generate_html_report(llm_results, human_results, args.output)

        print(f"✓ Comparison report generated: {args.output}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
```

**Step 2: Make script executable**

Run: `chmod +x /Users/stagcto/fyp/llm-testing/generate_comparison_report.py`

**Step 3: Test script**

Run: `cd /Users/stagcto/fyp/llm-testing && python generate_comparison_report.py --help`
Expected: Help message displays

**Step 4: Commit**

```bash
git add llm-testing/generate_comparison_report.py
git commit -m "feat: add comparison report generator for LLM vs human testing"
```

---

## Task 8: Update Documentation

**Files:**
- Create: `/Users/stagcto/fyp/docs/human-llm-testing-alignment.md`

**Step 1: Create documentation**

```markdown
# Human-LLM Testing Alignment

## Overview

This document describes the aligned testing framework that enables direct comparison between LLM-simulated conversations and human testing sessions.

## Key Features

### 1. Scenario-Guided Testing
- Humans can select scenarios before testing (matching LLM framework)
- 5 scenarios available: eSIM Setup, Roaming Activation, Billing Dispute, Plan Upgrade, Network Issue
- Scenario context displayed to guide conversation

### 2. Rubric-Aligned Feedback
- Both human and LLM testing use identical evaluation criteria
- **Task Success** (50% weight): Did assistant help accomplish goal?
- **Clarity** (20% weight): How clear were responses?
- **Empathy** (20% weight): How well did assistant acknowledge situation?
- **Information Accuracy** (10% weight): Accurate info without unsupported claims?

### 3. LLM-as-Judge Evaluation
- Human transcripts evaluated using same LAJ system as simulated conversations
- Enables comparison of human self-ratings vs LAJ ratings
- Identifies rating biases and discrepancies

### 4. Unified Reporting
- Comprehensive comparison reports
- LLM vs human performance metrics
- Variant A vs B analysis across both testing types

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Testing Framework                         │
├────────────────────────┬────────────────────────────────────┤
│   LLM-Simulated        │        Human Testing               │
│                        │                                     │
│  • 20 personas         │  • Real users                      │
│  • 5 scenarios         │  • Optional scenario selection     │
│  • Automated execution │  • Manual conversation             │
│  • LAJ evaluation      │  • Self-rating + LAJ evaluation    │
└────────────────────────┴────────────────────────────────────┘
                              ▼
                ┌─────────────────────────────┐
                │   Comparison Report         │
                │                             │
                │  • Rubric score comparison  │
                │  • Self-rating vs LAJ       │
                │  • Variant A vs B           │
                │  • Methodology notes        │
                └─────────────────────────────┘
```

## Database Schema Changes

### participants table
```sql
ALTER TABLE participants
ADD COLUMN scenario_id TEXT;
```

### support_feedback table
```sql
ALTER TABLE support_feedback
ADD COLUMN scenario_id TEXT,
ADD COLUMN rating_task_success INTEGER CHECK (rating_task_success >= 1 AND rating_task_success <= 5),
ADD COLUMN rating_clarity INTEGER CHECK (rating_clarity >= 1 AND rating_clarity <= 5),
ADD COLUMN rating_empathy INTEGER CHECK (rating_empathy >= 1 AND rating_empathy <= 5),
ADD COLUMN rating_accuracy INTEGER CHECK (rating_accuracy >= 1 AND rating_accuracy <= 5);
```

## Usage

### Running Human Tests with Scenarios

1. Navigate to the VodaCare chat interface
2. Enter participant details and select group (A or B)
3. **Optional:** Select a scenario to guide your conversation
4. Conduct conversation naturally based on scenario context
5. Click "Finish" and complete feedback form with rubric ratings

### Evaluating Human Transcripts with LAJ

```bash
cd /Users/stagcto/fyp/llm-testing

# Evaluate specific session
python evaluate_human_transcripts.py --session-id abc123

# Evaluate all sessions
python evaluate_human_transcripts.py --all --output human_evaluations.json

# Filter by variant
python evaluate_human_transcripts.py --all --participant-group A
```

### Generating Comparison Reports

```bash
cd /Users/stagcto/fyp/llm-testing

python generate_comparison_report.py \
  --llm-results "outputs/exp_*.json" \
  --human-results "human_evaluations.json" \
  --output "comparison_report.html"
```

Open `comparison_report.html` in browser to view results.

## Interpretation Guide

### Rating Scale Normalization

**Human Self-Ratings:** 1-5 stars
- 1 star → 0.0 (normalized)
- 3 stars → 0.5 (normalized)
- 5 stars → 1.0 (normalized)

**LAJ Ratings:** 0.0-1.0 scale (native)

### Self-Rating Bias

**Positive bias:** Humans rate higher than LAJ
- Common for subjective dimensions (empathy, friendliness)
- May indicate generous self-assessment

**Negative bias:** Humans rate lower than LAJ
- Less common, may indicate high standards
- Could reflect frustration or unmet expectations

### Variant Comparison

**Expected patterns:**
- **Variant A (Kindness):** Higher empathy scores, more emotional language
- **Variant B (Confirmation):** Higher clarity scores, more structured responses

**Statistical significance:**
- Differences > 0.1 on 0-1 scale considered meaningful
- Look for consistent patterns across multiple dimensions

## Best Practices

### For Human Testing
1. Select scenario that matches your actual need
2. Read scenario context before starting
3. Rate honestly based on your experience
4. Complete all rubric questions for best analysis

### For LAJ Evaluation
1. Ensure sufficient conversation history (3+ turns recommended)
2. Run evaluation shortly after human testing completes
3. Review outliers (alignment < 50%) manually
4. Consider context when interpreting discrepancies

### For Reporting
1. Include both LLM and human results for fair comparison
2. Filter by variant (A/B) for targeted analysis
3. Normalize sample sizes when comparing metrics
4. Document testing conditions and participant demographics

## Limitations

1. **Generic LAJ Context:** Human conversations lack persona-specific context that simulated conversations have
2. **Self-Rating Bias:** Humans may rate differently based on mood, expectations, or understanding of scale
3. **Sample Size:** Human testing typically has smaller sample size than LLM simulation
4. **Scenario Adherence:** Humans may deviate from scenario guidance more than simulated personas

## Future Enhancements

- [ ] Pre/post-conversation questionnaire for human participants
- [ ] Session recording for qualitative analysis
- [ ] Demographic-based segmentation for human results
- [ ] Real-time LAJ feedback during human testing
- [ ] A/B randomization (automated group assignment)

## References

- LLM Testing Framework: `/Users/stagcto/fyp/llm-testing/`
- System Prompts: `/Users/stagcto/fyp/sys_prompt_a.txt`, `/Users/stagcto/fyp/sys_prompt_b.txt`
- Evaluation Rubric: `/Users/stagcto/fyp/llm-testing/config/evaluation_rubric.yaml`
- API Models: `/Users/stagcto/fyp/server/app/models.py`
```

**Step 2: Update main README**

Append to `/Users/stagcto/fyp/README.md`:

```markdown

## Human-LLM Testing Alignment

This project includes aligned testing frameworks for both LLM-simulated and human testing.

### Features
- Scenario-guided human testing matching LLM framework
- Rubric-aligned feedback collection (Task Success, Clarity, Empathy, Accuracy)
- LLM-as-Judge evaluation of human transcripts
- Unified comparison reports

### Documentation
See [docs/human-llm-testing-alignment.md](docs/human-llm-testing-alignment.md) for full details.

### Quick Start

**Run LLM Testing:**
```bash
cd llm-testing
python run_experiment.py --variant A --personas all --scenarios all
```

**Evaluate Human Transcripts:**
```bash
cd llm-testing
python evaluate_human_transcripts.py --all --output human_evals.json
```

**Generate Comparison Report:**
```bash
cd llm-testing
python generate_comparison_report.py \
  --llm-results "outputs/exp_*.json" \
  --human-results "human_evals.json" \
  --output "report.html"
```
```

**Step 3: Commit**

```bash
git add docs/human-llm-testing-alignment.md README.md
git commit -m "docs: add human-LLM testing alignment documentation"
```

---

## Testing & Validation

### Integration Test: End-to-End Flow

**Step 1: Apply database migration**

Run SQL from `/Users/stagcto/fyp/server/migrations/add_scenario_and_rubric_fields.sql` in Supabase dashboard

**Step 2: Start servers**

```bash
# Terminal 1: Backend
cd /Users/stagcto/fyp/server
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd /Users/stagcto/fyp/web
npm run dev
```

**Step 3: Test human workflow**

1. Navigate to http://localhost:3000
2. Enter name and select group A
3. Select scenario "EU Roaming Activation"
4. Verify scenario context displays
5. Start chat and ask about roaming
6. Complete conversation (3+ turns)
7. Click "Finish" button
8. Verify feedback modal shows:
   - Original 3 ratings (overall, helpfulness, friendliness)
   - New rubric section with 4 ratings
9. Submit feedback
10. Verify success message

**Step 4: Test LAJ evaluation**

```bash
cd /Users/stagcto/fyp/llm-testing

# Get session ID from browser localStorage or Supabase
python evaluate_human_transcripts.py --session-id <session-id>

# Verify output JSON contains:
# - transcript
# - human_feedback with rubric ratings
# - laj_evaluation with scores
# - comparison with alignment metrics
```

**Step 5: Test comparison report**

```bash
# Ensure you have both LLM and human results
python generate_comparison_report.py \
  --llm-results "outputs/exp_*.json" \
  --human-results "human_evaluations.json" \
  --output "test_report.html"

# Open test_report.html in browser
# Verify all sections render correctly
```

**Step 6: Verify data persistence**

Check Supabase tables:
- `participants`: scenario_id populated
- `support_feedback`: rubric rating columns populated
- `messages`: conversation stored correctly

---

## Summary

This plan implements comprehensive human-LLM testing alignment:

1. ✅ Backend models updated for scenario and rubric support
2. ✅ Scenarios API endpoint for frontend consumption
3. ✅ Database schema migration with rubric columns
4. ✅ Frontend enrollment form with scenario selection
5. ✅ Feedback modal enhanced with rubric ratings
6. ✅ LAJ evaluation script for human transcripts
7. ✅ Comparison report generator (HTML)
8. ✅ Complete documentation

**Key Benefits:**
- Direct comparison between simulated and human testing
- Self-rating vs LAJ rating analysis
- Unified evaluation rubric across testing types
- Rich comparison reports for decision-making

**Files Modified:** 11
**Files Created:** 5
**Total Implementation Time:** ~3-4 hours
