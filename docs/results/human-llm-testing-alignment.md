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
- **Task Success** (60% weight): Did assistant help accomplish goal?
- **Clarity** (20% weight): How clear were responses?
- **Empathy** (20% weight): How well did assistant acknowledge situation?

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

## Results (2026-02-24)

> 83 sessions · 676 messages · 88 feedback entries. LAJ run: `human_laj_combined_analysis.py`.

### Dataset

| Group | Sessions | Messages | Feedback entries |
|---|---|---|---|
| A (Kindness prompt) | 52 | 388 | 52 |
| B (Confirmation prompt) | 36 | 288 | 36 |
| **Total** | **83** | **676** | **88** |

### LLM-as-Judge Scores (0–1)

| Metric | Group A | Group B | Δ (A − B) |
|---|---|---|---|
| **Overall** | **0.89** | **0.82** | +0.07 |
| Task Success | 0.83 | 0.83 | ≈ equal |
| Clarity | 0.91 | 0.89 | +0.02 |
| **Empathy** | **0.96** | **0.60** | **+0.36** |

### Human Self-Ratings (1–5)

| Metric | Group A | Group B | Δ (A − B) |
|---|---|---|---|
| **Overall** | **3.90** | **3.91** | ≈ equal |
| Task Success | 4.06 | 4.06 | ≈ equal |
| Clarity | 4.04 | 3.91 | +0.13 |
| **Empathy** | **4.50** | **3.90** | **A +0.60** |
| Accuracy | 4.04 | 3.88 | +0.16 |

### LAJ vs Self-Rating Comparison (normalised to 0–1)

| Metric | A — LAJ | A — Self | B — LAJ | B — Self |
|---|---|---|---|---|
| Overall | 0.89 | 0.78 | 0.82 | 0.78 |
| Task Success | 0.83 | 0.81 | 0.83 | 0.81 |
| Clarity | 0.91 | 0.81 | 0.89 | 0.78 |
| **Empathy** | **0.96** | **0.90** | **0.60** | **0.78** |

---

### Human Feedback Analysis

#### Rating distributions

**Group A** (50 rated sessions out of 52):

| Rating | Overall | Task Success | Clarity | Accuracy |
|---|---|---|---|---|
| 5 | 13 (26%) | 24 (48%) | 20 (41%) | 16 (33%) |
| 4 | 25 (50%) | 11 (22%) | 18 (37%) | 24 (49%) |
| 3 | 7 (14%) | 10 (20%) | 5 (10%) | 5 (10%) |
| 2 | 4 (8%) | 4 (8%) | 5 (10%) | 3 (6%) |
| 1 | 1 (2%) | 1 (2%) | 1 (2%) | 1 (2%) |

76% of Group A users rated overall satisfaction 4 or 5. Task success is notably bimodal — nearly half gave 5 stars, but 30% gave 3 or below, reflecting the billing scenario limitation where users wanted a direct fix that wasn't possible.

**Group B** (33 rated sessions out of 36):

| Rating | Overall | Task Success | Clarity | Accuracy |
|---|---|---|---|---|
| 5 | 9 (27%) | 13 (39%) | 9 (27%) | 8 (24%) |
| 4 | 17 (52%) | 12 (36%) | 15 (45%) | 15 (45%) |
| 3 | 3 (9%) | 5 (15%) | 6 (18%) | 9 (27%) |
| 2 | 3 (9%) | 3 (9%) | 3 (9%) | 0 (0%) |
| 1 | 1 (3%) | 0 (0%) | 0 (0%) | 1 (3%) |

79% of Group B users rated overall satisfaction 4 or 5 — almost identical to Group A. No user in Group B gave clarity or task success a 1-star rating, suggesting responses were perceived as at least minimally competent across the board.

#### Where users were dissatisfied

Both groups produced a small cluster of low-rated sessions (overall ≤ 2): 5 in Group A and 4 in Group B. These all share the same root cause: the assistant could not access account details to resolve a billing dispute or explain a specific unexpected charge. Users wanted a direct explanation or correction; the assistant instead provided generic steps and referred them to customer support. Users consistently rate this as a failure regardless of how well the assistant communicated.

One notable pattern: in several of these low-rated sessions the LAJ still scored the overall interaction reasonably high (0.70–0.94), because the assistant followed correct procedure and was technically helpful. This is the most significant divergence between human and LAJ scoring. A user who wanted their bill fixed and was told to call support will give a 1–2 overall regardless of how clearly or empathetically the assistant delivered that message.

#### What users actually valued

Looking at where users awarded 5 stars on task success (48% in Group A, 39% in Group B), these are almost exclusively sessions where the assistant guided them step-by-step to a concrete outcome — eSIM activated, roaming confirmed, plan upgraded. The resolution itself drives the top rating; once the issue is resolved users are generous across all dimensions.

The clarity and accuracy scores track closely with each other and with overall, suggesting users do not sharply distinguish between "the answer was right" and "I understood it." These two dimensions appear to capture the same perceived quality from a user's perspective.

#### Empathy self-ratings

The empathy rating is stored as a composite score on a different numeric scale to the other dimensions — values exceed 5.0, indicating it is an average of multiple sub-questions. Directional comparisons between groups are valid; absolute comparison to the 1–5 integer dimensions is not. Group A scores 4.50 and Group B scores 3.90 — a gap of 0.60 — meaning users in Group A perceived the assistant as noticeably more empathetic. This aligns with the LAJ empathy finding (0.96 vs 0.60) and is the largest disagreement between the two groups on any user-facing dimension.

---

### Qualitative Analysis (from LAJ rationale)

#### Task Success — both groups

Task success failures are scenario-driven rather than variant-driven, which explains why the averages are identical (0.83). The pattern is consistent across both groups:

- **Billing disputes** are the weakest scenario for both variants. The assistant cannot access account details, so it falls back to generic steps ("check your bill", "contact support"), leaving users without a concrete resolution. The judge consistently flags this: *"the assistant provided general guidance on how to address the unexpected charges but did not directly assist the user in resolving their specific issue."* Scores typically 0.4–0.5 for these sessions.
- **eSIM setup, roaming, and plan upgrades** score highest (0.8–1.0) in both groups. The assistant's domain knowledge on these is strong and it guides users to successful outcomes.
- **Network troubleshooting** scores moderately (0.7–0.9). The assistant provides actionable steps but cannot guarantee resolution, and the judge penalises when the user reports the problem persists without the assistant escalating or suggesting a SIM replacement.
- In a small number of sessions (both groups), responses were cut off mid-explanation, leaving the user without complete information and capping task success at 0.8 regardless of quality.

One Group B-specific task failure: a session where the assistant initially told the user to *"ask the customer"* about billing errors — confusing the roles of customer and support agent — before self-correcting. This produced a clarity score of 0.6 and indicates the confirmation-style prompt can produce confused output when the instruction context is ambiguous. Another Group B session gave contradictory data allowance figures (10 GB UK vs 5 GB roaming) without clearly reconciling them, again lowering clarity.

#### Empathy — the key differentiator

This is where the two variants diverge sharply, and uniquely, all three evaluation methods agree: simulation LAJ (0.844 vs 0.545), human LAJ (0.96 vs 0.60), and human self-rating (4.50 vs 3.90).

**Group A** responses are characterised by explicit emotional acknowledgment throughout the conversation. The judge repeatedly cites language like *"I'm really sorry to hear that"*, *"I truly empathize with how frustrating this must be"*, *"It's completely understandable to feel overwhelmed"*, and active reassurance when users express confusion or distress. Across eSIM, billing, and network scenarios alike, Group A sessions score 0.9–1.0 on empathy because the assistant addresses not just the problem but the user's emotional state at each turn.

**Group B** responses answer questions accurately and politely but consistently fail to acknowledge user frustration or uncertainty in a personal way. The judge's recurring verdict: *"responses felt more procedural than supportive"*, *"lack of warmth or personal connection"*, *"while the assistant was polite and confirmed understanding, there was a lack of personalised empathy"*. In billing disputes — where users are already frustrated — this is especially penalised: scores of 0.4 appear where the assistant processes the request competently but never validates the user's frustration. In roaming and plan sessions, Group B scores 0.5 even when task success is 1.0, because the assistant provides accurate information without acknowledging that travel or cost concerns might be stressful.

The judge does not penalise Group B for being unhelpful — it penalises it for being impersonal. Critically, users in Group B also noticed this: their self-rated empathy score (3.90) is the lowest dimension across either group, and the gap from Group A (4.50) is the largest user-rated difference in the study. The Kindness prompt demonstrably produces more empathetic responses by every available measure.

---

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
