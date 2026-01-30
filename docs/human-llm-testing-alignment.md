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
