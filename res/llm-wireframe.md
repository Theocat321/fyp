# LLM Simulation & A/B Testing — Requirements Wireframe (No Code)

## 1) Purpose

* Evaluate two chatbot variants (A and B) against a diverse, fixed set of personas for a Vodafone-style mobile support use case.
* Produce reliable, comparable insights across time (long-run regression detection, drift, robustness).
* Optimize for both **resolution quality** and **customer experience**.



## 2) Scope

**In-scope**

* Persona library (20 diverse profiles; fixed IDs; stable definitions).
* Scenario library (common tasks like eSIM, roaming, billing, upgrade, cancellation, SIM swap).
* Variant management (A/B prompts and runtime parameters).
* Conversation orchestration (multi-turn, termination criteria, retries).
* Judging and scoring (LLM rubric + deterministic heuristics).
* Metrics, storage, reporting, and experiment governance.

**Out-of-scope**

* Live routing of production traffic.
* Human annotation at scale.
* Automated remediation in production.



## 3) Core Components

### 3.1 Persona Registry

* Persistent set of 20 named personas with:

  * ID, name, demographics (age, location), tech literacy, tone/style.
  * Primary goal(s) and typical constraints (time pressure, language mixing, accessibility needs).
  * Seed utterance (first message) and behavior modifiers (impatient, repeats, bilingual, etc.).
* Governance: changes only via versioned releases; no ad-hoc edits.

### 3.2 Scenario Library

* Canonical tasks grouped by topic (roaming, billing, device, network, account, retention).
* For each scenario:

  * ID, title, topic, happy-path tasks, common edge cases, explicit success criteria.
* Coverage targets: each persona × multiple scenarios over time, balanced per variant.

### 3.3 Variant Definitions

* Variant A: “Structured Service Expert” (formal, concise, stepwise).
* Variant B: “Empathetic Support Partner” (supportive, clear, human-like).
* Fixed prompt texts and stable runtime parameters (temperature, etc.).
* Versioning and change log.

### 3.4 Conversation Orchestrator

* Drives multi-turn dialogues until termination condition.
* Maintains strict message ordering and persona consistency.
* Enforces max turns and timeouts; records all meta (latency, turns, retries).
* Supports deterministic run planning (seeded randomization).

### 3.5 Judges & Scoring

* LLM selects sentiment as it goes (good or bad message)
* LLM completes the same human form at the end

### 3.6 Metrics & Reporting

* Aggregates by variant, persona, scenario, topic, and time window.
* Perhaps control charts / trend views to catch regressions.

### 3.7 Storage & Artifacts

* Immutable run records: prompts (system/variant), persona snapshot, scenario snapshot, full transcript, scores, heuristics, timings.
* Indexing: experiment ID, variant ID, persona ID, scenario ID, run number.
* Retention policy and PII control (no real customer data; synthetic only).



## 4) Data Model (field lists, no code)

### 4.1 Persona

* `id` (stable), `name`
* `demographics` (age, location)
* `tech_literacy` (low/moderate/high)
* `tone_style` (e.g., angry_impatient, polite_confused, bilingual_DE_EN)
* `goals` (list)
* `constraints` (e.g., time_pressure, accessibility_required, language_mixing)
* `seed_utterance` (first message)
* `behavior_modifiers` (e.g., repeats_self, escalates_if_slow)

### 4.2 Scenario

* `id`, `title`, `topic`
* `happy_path` (ordered steps)
* `edge_cases` (common detours)
* `success_criteria` (explicit, verifiable)

### 4.3 Experiment Config (logical fields)

* `experiment_id`
* `variants` (A, B) with references to fixed system prompts and runtime params
* `personas` reference (list of persona IDs or file path)
* `scenarios` reference (list of scenario IDs or file path)
* Conversation limits: `max_turns`, `turn_timeout`, `retry_policy`
* Routing/balancing: randomization method (e.g., blocked by topic)
* Judging: rubric reference, weightings
* Storage: output location and retention flags

### 4.4 Run Record

* `run_id` (composed key: experiment/variant/persona/scenario/sequence)
* `variant_id`, `persona_id`, `scenario_id`
* `seed`, `start_timestamp`, `end_timestamp`
* `turns` (count), `latency_ms` (avg, p95), `timeouts`, `retries`
* Transcript (ordered roles and content)
* Termination reason (success, ambiguity, max_turns, escalation)

### 4.5 Evaluation Record

* Scores: task_success, clarity, empathy, policy_compliance, overall
* Judge rationale (short paragraph)
* Heuristics: steps_count, contains_apology (bool), escalation_offered (bool), forbidden_claims (bool), off_topic_ratio
* Flags: needs_manual_review (bool), drift_suspected (bool)



## 5) Conversation Policies

* **Never hallucinate** plan details, prices, coverage maps; if uncertain, state limits and propose escalation.
* **Privacy & safety**: never request sensitive PII beyond what a standard support flow genuinely requires (and only in synthetic form).
* **Clarity**: end each assistant message with a next step or confirmation question.
* **Empathy** (variant B emphasis): acknowledge emotion before instructions.
* **Accessibility**: provide screen-reader friendly, step-by-step guidance when persona requires it.
* **Termination**: stop when success criteria met or when escalation is clearly the right next step.



## 6) Evaluation Rubric (scales 0.0–1.0)

* **Task Success (50%)**: Did the dialogue meet the scenario’s success criteria?
* **Clarity (20%)**: Steps concise, ordered, and understandable to the persona’s literacy level.
* **Empathy (20%)**: Appropriate acknowledgment and tone for the persona’s state.
* **Policy Compliance (10%)**: No prohibited claims; correct safety/privacy posture.

**Heuristic gates (pass/fail)**

* No unsupported technical claims.
* No contradictory instructions across turns.
* Escalation offered when required (e.g., SIM swap/fraud cases).



## 7) Experiment Design & Scheduling

* **Blocking**: Balance A/B per topic and persona to avoid confounding.
* **Seeding**: Fixed seeds per persona × scenario × variant for reproducibility, updated only on version bump.
* **Cadence**: Daily or weekly batches to catch regressions; include a fixed “sanity panel” subset for trend tracking.
* **Versioning**: Any change to prompts, personas, or judge rubric increments experiment version and archives all artifacts.



## 8) Reporting Requirements

* **Per-variant dashboards**: overall score trend, task_success trend, sentiment proxies.
* **Breakdowns**: by persona, scenario, topic; surface worst cohorts and outliers.
* **Top failure reasons**: frequent termination causes, common edge-case misses.
* **Compare view**: A vs B deltas for each metric and cohort, with significance hints.
* **Drift alerts**: when judge distributions shift vs the calibration set.



## 9) Risks & Mitigations

* **Judge drift** → Maintain a frozen calibration set and track judge agreement with known outcomes.
* **Persona collapse** (LLM responds same way to different personas) → Enforce strong persona constraints and audit linguistic markers.
* **Overfitting to tests** → Rotate scenarios, introduce unseen edge cases periodically.
* **Metric gaming** → Keep a mix of human-interpretable rationale plus heuristics; sample manual audits.



## 10) Acceptance Criteria

* Runs produce complete artifacts (prompts, transcripts, scores) with zero missing fields.
* A/B comparisons stable across at least two independent batches.
* At least one actionable insight per topic area (e.g., “Variant B under-escalates SIM-swap fraud”).
* Dashboards show pass/fail gates, top regressions, and explainability snippets.



## 11) Single-Persona Flow (Textual Diagram)

**Persona:** Frustrated Commuter
**Scenario:** Fix poor signal on train
**Variant:** A or B (as assigned)

1. Initialize run → assign `experiment_id`, `variant_id`, `persona_id`, `scenario_id`, seed.
2. Load fixed variant prompt; snapshot persona and scenario definitions.
3. Start conversation:

   * User turn 1 (seed utterance): “Signal drops on my commute. Fix it now.”
   * Assistant turn 1: confirms intent, gathers essentials (location/route, time window, device/network mode).
4. User turn 2: provides minimal info, expresses impatience.
5. Assistant turn 2: gives targeted checks (network mode, Wi-Fi calling off, 4G/5G toggle) and asks for a result.
6. User turn 3: partial success or new symptom (e.g., calls okay, data poor).
7. Assistant turn 3: next diagnostic layer (APN verification, coverage advisory, known maintenance; propose offline logs if needed).
8. Termination test:

   * If success criteria met (stable data across route): assistant summarizes fix and confirms closure.
   * Else: assistant proposes escalation (ticket with location/time windows, cell IDs if available).
9. Judge evaluation:

   * LLM rubric scores + heuristics (steps count, apology presence, escalation offered).
10. Persist artifact:

* Transcript, timings, scores, rationale, termination reason.

11. Aggregate metrics:

* Update dashboards and cohort deltas (persona × topic × variant).

12. Alerts (if configured):

* Flag regressions vs last stable experiment.


## 12) Experiment Checklist

* Persona and scenario libraries frozen and reviewed.
* Variant prompts and parameters frozen and versioned.
* Dry-run with small batch confirms artifact completeness and scoring stability.

