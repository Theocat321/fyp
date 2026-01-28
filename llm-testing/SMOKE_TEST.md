# Smoke Test - Quick Validation

## Quick 3-Persona Test (1 Scenario)

**Total: 6 conversations** (3 personas × 1 scenario × 2 variants)
**Time:** ~10-15 minutes
**Cost:** ~$3-5

### Test Set
- **Personas:** Frustrated Commuter (angry), Elderly Newbie (polite), Teen Gamer (casual)
- **Scenario:** Network Issue (troubleshooting)
- **Both variants:** A and B

---

## Run Smoke Test

```bash
cd /Users/stagcto/fyp/llm-testing
source venv/bin/activate

# Variant A (3 conversations)
python3 run_experiment.py \
  --variant A \
  --personas persona_01_frustrated_commuter,persona_02_elderly_tech_newbie,persona_03_teen_gamer \
  --scenarios scenario_005_network_issue \
  --name "smoke_test_variant_a"

# Variant B (3 conversations)
python3 run_experiment.py \
  --variant B \
  --personas persona_01_frustrated_commuter,persona_02_elderly_tech_newbie,persona_03_teen_gamer \
  --scenarios scenario_005_network_issue \
  --name "smoke_test_variant_b"
```

---

## What to Check

### 1. Conversations Complete
```bash
# Check output files exist
ls -lh outputs/exp_*_smoke_test_*.json
ls -lh outputs/summary_*_smoke_test_*.json
```

### 2. View Summaries
```bash
# Variant A summary
cat outputs/summary_A_smoke_test_*.json | jq '.summary'

# Variant B summary
cat outputs/summary_B_smoke_test_*.json | jq '.summary'
```

### 3. Quick Comparison
```bash
echo "=== VARIANT A ===" && \
cat outputs/summary_A_smoke_test_*.json | jq '{
  total: .summary.total_conversations,
  avg_empathy: .summary.avg_empathy,
  avg_clarity: .summary.avg_clarity,
  avg_task_success: .summary.avg_task_success,
  avg_overall: .summary.avg_overall_score
}'

echo -e "\n=== VARIANT B ===" && \
cat outputs/summary_B_smoke_test_*.json | jq '{
  total: .summary.total_conversations,
  avg_empathy: .summary.avg_empathy,
  avg_clarity: .summary.avg_clarity,
  avg_task_success: .summary.avg_task_success,
  avg_overall: .summary.avg_overall_score
}'
```

### 4. Read One Transcript
```bash
# View one conversation transcript
cat outputs/exp_A_smoke_test_*.json | jq '.conversations[0] | {
  persona: .persona_id,
  scenario: .scenario_id,
  turns: .total_turns,
  termination: .termination.reason,
  scores: .llm_evaluation
}' | less
```

---

## Success Criteria

- [x] Both files created (variant A and B)
- [x] 3 conversations in each file
- [x] Scores are in range 0.0-1.0
- [x] Conversations have 2-10 turns (not all hitting max)
- [x] Different personas show different behavior
- [x] No critical errors in `experiment.log`

---

## If Smoke Test Passes

✅ **You're ready for main data collection!**

Proceed to `RUN_TRACKER.md` for systematic collection.

---

## If Issues Found

Check `experiment.log`:
```bash
tail -50 experiment.log
```

Common issues:
- OpenAI API key not set
- VodaCare server not running
- Network connectivity issues
