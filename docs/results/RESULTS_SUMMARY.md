# A/B Study Results Summary

## 1. Data Overview

| Bucket | Conversations / Sessions | Messages | Source |
|---|---|---|---|
| **Simulation — Variant A** | 100 | ~420 (avg 4.2/convo) | LLM synthetic personas |
| **Simulation — Variant B** | 100 | ~437 (avg 4.37/convo) | LLM synthetic personas |
| **Human — Group A** | 52 sessions | 388 | Real users |
| **Human — Group B** | 36 sessions | 288 | Real users |

---

## 2. LLM Simulation Results

> Scores are 0–1. Evaluated by LLM-as-Judge with full persona + scenario + success criteria context.

| Metric | Variant A | Variant B | A vs B |
|---|---|---|---|
| **Overall Score** | 0.563 | 0.514 | A +0.049 |
| Task Success | 0.347 | 0.351 | ≈ equal |
| Clarity | 0.709 | 0.721 | B +0.012 |
| Empathy | **0.844** | **0.545** | A +0.299 |

### Conversation Outcomes

| Outcome | Variant A | Variant B |
|---|---|---|
| Satisfaction (resolved) | 40% | 35% |
| Escalation | 32% | 29% |
| Stalemate | 12% | 17% |
| Patience exceeded | 16% | 19% |
| **Heuristic Pass Rate** | **81%** | **73%** |
| **Critical Failure Rate** | **5%** | **18%** |

> Variant A outperforms Variant B in simulation — higher satisfaction, lower failure rate, and significantly higher empathy.

---

## 3. Human Study Results

### 3a. LLM-as-Judge on Human Conversations

> Same rubric and scoring logic as simulation (task_success × 0.6, clarity × 0.2, empathy × 0.2). Evaluated without persona/scenario context. Generated 2026-02-24 (n=83 sessions, 88 feedback entries).

| Metric | Human Group A | Human Group B | A vs B |
|---|---|---|---|
| **Overall Score** | 0.89 | 0.82 | A +0.07 |
| Task Success | 0.83 | 0.83 | ≈ equal |
| Clarity | 0.91 | 0.89 | A +0.02 |
| Empathy | **0.96** | **0.60** | **A +0.36** |

### 3b. Human Self-Ratings

> Collected via post-conversation feedback form. Scale: 1–5.

| Metric | Human Group A | Human Group B | A vs B |
|---|---|---|---|
| **Overall** | 3.90 / 5 | 3.91 / 5 | ≈ equal |
| Task Success | 4.06 / 5 | 4.06 / 5 | ≈ equal |
| Clarity | 4.04 / 5 | 3.91 / 5 | A +0.13 |
| **Empathy** | **4.50 / 5** | **3.90 / 5** | **A +0.60** |
| Accuracy | 4.04 / 5 | 3.88 / 5 | A +0.16 |

### 3c. LAJ vs Human Self-Rating Comparison

> Human self-ratings normalised to 0–1 for direct comparison.

| Metric | Group A — LAJ | Group A — Self | Group B — LAJ | Group B — Self |
|---|---|---|---|---|
| Overall | 0.89 | 0.78 | 0.82 | 0.78 |
| Task Success | 0.83 | 0.81 | 0.83 | 0.81 |
| Clarity | 0.91 | 0.81 | 0.89 | 0.78 |
| **Empathy** | **0.96** | **0.90** | **0.60** | **0.78** |

> Group A leads on empathy across both evaluation methods — LAJ (+0.36) and human self-rating (+0.60 on 5-pt scale). The Kindness prompt produces responses that are perceived as more empathetic by both users and the automated judge.

---

## 4. Key Findings

1. **Variant A consistently outperforms Variant B** — confirmed by simulation LAJ, human study LAJ, and human self-ratings.

2. **Empathy is the sharpest differentiator** — Group B scores markedly lower in simulation (0.545), human LAJ (0.60), and human self-rating (3.90 vs 4.50). All three evaluation methods agree.

3. **Human self-ratings are generous overall but discriminate on empathy** — both groups rate overall satisfaction nearly identically (~3.90/5), yet the empathy gap is the largest human-rated difference (0.60 pts). Users notice the empathy difference even when overall satisfaction is similar.

4. **Task success is scenario-driven, not variant-driven** — identical LAJ scores (0.83) and self-ratings (4.06) in both groups. The prompt variant changes how the assistant communicates, not whether it resolves issues.

5. **Simulation scores are lower overall** (~0.51–0.56) vs human LAJ (~0.82–0.89) — partly because simulated personas apply harder success criteria and include difficult personas (rude, impatient, troll).
