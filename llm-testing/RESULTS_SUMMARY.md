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

> Same rubric and scoring logic as simulation (task_success × 0.5, clarity × 0.2, empathy × 0.2, policy_compliance × 0.1). Evaluated without persona/scenario context. Generated 2026-02-24 (n=83 sessions, 88 feedback entries).

| Metric | Human Group A | Human Group B | A vs B |
|---|---|---|---|
| **Overall Score** | 0.89 | 0.82 | A +0.07 |
| Task Success | 0.83 | 0.83 | ≈ equal |
| Clarity | 0.91 | 0.89 | A +0.02 |
| Empathy | **0.94** | **0.65** | A +0.29 |

### 3b. Human Self-Ratings

> Collected via post-conversation feedback form. Scale: 1–5.

| Metric | Human Group A | Human Group B | A vs B |
|---|---|---|---|
| **Overall** | 3.90 / 5 | 3.91 / 5 | ≈ equal |
| Task Success | 4.06 / 5 | 4.06 / 5 | ≈ equal |
| Clarity | 4.04 / 5 | 3.91 / 5 | A +0.13 |
| Empathy | 4.14 / 5 | **4.33 / 5** | B +0.19 |
| Accuracy | 4.04 / 5 | 3.88 / 5 | A +0.16 |

### 3c. LAJ vs Human Self-Rating Comparison

> Human self-ratings normalised to 0–1 for direct comparison.

| Metric | Group A — LAJ | Group A — Self | Group B — LAJ | Group B — Self |
|---|---|---|---|---|
| Overall | 0.89 | 0.78 | 0.82 | 0.78 |
| Task Success | 0.83 | 0.81 | 0.83 | 0.81 |
| Clarity | 0.91 | 0.81 | 0.89 | 0.78 |
| **Empathy** | **0.94** | **0.83** | **0.65** | **0.87** |

> **Notable discrepancy on empathy in Group B:** Human self-raters scored Group B empathy higher than Group A (4.33/5 = 0.87), while the LAJ scored it lower (0.65 vs 0.94). This suggests users *felt* the assistant was empathetic but the LLM judge detected a lack of genuine understanding or personalisation in the responses.

---

## 4. Key Findings

1. **Variant A consistently outperforms Variant B** — confirmed by both simulation LAJ and human study LAJ.

2. **Empathy is the sharpest differentiator** between variants — Variant B / Group B scores markedly lower in both simulation (0.545) and human LAJ (0.61).

3. **Human self-ratings are more generous and less discriminating** — both groups rated similarly (~3.9–4.0/5 overall), while LAJ detected a clearer gap.

4. **The empathy paradox in Group B** — humans rated Group B empathy *higher* (4.33/5) than Group A (4.14/5), yet the LAJ rated it much lower (0.65 vs 0.94). Suggests surface-level warmth that doesn't translate to substantive help.

5. **Simulation scores are lower overall** (~0.51–0.56) vs human LAJ (~0.81–0.89) — partly because simulated personas apply harder success criteria and include difficult personas (rude, impatient, troll).
