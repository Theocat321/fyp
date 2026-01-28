# Data Collection Checklist

## Phase 1: Setup & Validation (10 minutes)

### 1.1 Add Your OpenAI API Key
```bash
cd /Users/stagcto/fyp/llm-testing
nano .env  # or use your preferred editor
```

Update this line with your real key:
```
OPENAI_API_KEY=sk-your-actual-openai-key-here
```

**Cost estimate**:
- Single conversation: ~$0.50-1.00
- Full run (100 conversations): ~$50-100

### 1.2 Start VodaCare Server
```bash
# In a separate terminal
cd /Users/stagcto/fyp/server
uvicorn app.main:app --reload
```

Verify it's running:
```bash
curl http://localhost:8000/health
```

### 1.3 Test Single Conversation
```bash
cd /Users/stagcto/fyp/llm-testing
source venv/bin/activate

# Quick test - should take 2-3 minutes
python3 run_experiment.py \
  --variant A \
  --personas persona_01_frustrated_commuter \
  --scenarios scenario_005_network_issue \
  --name "pre_flight_test" \
  --log-level DEBUG
```

**Expected output:**
- Turn-by-turn conversation progress
- Evaluation scores (0.0-1.0)
- Files created in `outputs/` directory

**If it works:** ✅ Proceed to Phase 2
**If it fails:** Check `experiment.log` for errors

---

## Phase 2: Pilot Study (30 minutes)

### 2.1 Small Pilot Run
Test a subset to validate your design:

```bash
# Variant A - 5 personas × 3 scenarios = 15 conversations
python3 run_experiment.py \
  --variant A \
  --personas persona_01,persona_02,persona_03,persona_09,persona_19 \
  --scenarios scenario_001,scenario_003,scenario_005 \
  --name "pilot_variant_a"

# Variant B - same personas/scenarios
python3 run_experiment.py \
  --variant B \
  --personas persona_01,persona_02,persona_03,persona_09,persona_19 \
  --scenarios scenario_001,scenario_003,scenario_005 \
  --name "pilot_variant_b"
```

**Why pilot?**
- Validates experimental setup
- Checks if conversations are realistic
- Tests evaluation metrics
- Estimates time and cost

**Time:** ~30-45 minutes total
**Cost:** ~$10-15

### 2.2 Review Pilot Results
```bash
# View summary
cat outputs/summary_A_pilot_variant_a_*.json | jq '.summary'
cat outputs/summary_B_pilot_variant_b_*.json | jq '.summary'

# Quick comparison
echo "Variant A empathy:" && cat outputs/summary_A_*.json | jq '.summary.avg_empathy'
echo "Variant B empathy:" && cat outputs/summary_B_*.json | jq '.summary.avg_empathy'
```

**Check for:**
- [ ] Conversations seem realistic (read 2-3 transcripts)
- [ ] Evaluation scores are reasonable (not all 0 or all 1)
- [ ] Different personas behave differently
- [ ] No technical errors in logs

---

## Phase 3: Main Data Collection

### Option A: Conservative (Recommended for Undergrad)
**60 conversations** = 10 personas × 3 scenarios × 2 variants

**Selected personas** (diverse mix):
- persona_01 (frustrated commuter - angry, moderate tech)
- persona_02 (elderly newbie - polite, low tech)
- persona_03 (teen gamer - casual, high tech)
- persona_06 (student budgeter - skeptical)
- persona_08 (family organizer - chatty)
- persona_09 (rage quitter - aggressive)
- persona_12 (accessibility user - specific needs)
- persona_17 (bargain hunter - strategic)
- persona_18 (loyal customer - emotional appeal)
- persona_19 (fraud victim - panicked)

**Selected scenarios**:
- scenario_001 (eSIM setup - straightforward)
- scenario_003 (billing dispute - emotional)
- scenario_005 (network issue - troubleshooting)

```bash
# Variant A
python3 run_experiment.py \
  --variant A \
  --personas persona_01,persona_02,persona_03,persona_06,persona_08,persona_09,persona_12,persona_17,persona_18,persona_19 \
  --scenarios scenario_001,scenario_003,scenario_005 \
  --name "main_study_variant_a"

# Variant B
python3 run_experiment.py \
  --variant B \
  --personas persona_01,persona_02,persona_03,persona_06,persona_08,persona_09,persona_12,persona_17,persona_18,persona_19 \
  --scenarios scenario_001,scenario_003,scenario_005 \
  --name "main_study_variant_b"
```

**Time:** ~2-3 hours total
**Cost:** ~$30-40

---

### Option B: Comprehensive
**100 conversations** = 20 personas × 5 scenarios × 1 variant (run twice for both)

```bash
# Variant A - all personas, all scenarios
python3 run_experiment.py \
  --variant A \
  --personas all \
  --scenarios all \
  --name "full_study_variant_a"

# Variant B - all personas, all scenarios
python3 run_experiment.py \
  --variant B \
  --personas all \
  --scenarios all \
  --name "full_study_variant_b"
```

**Time:** ~4-6 hours total
**Cost:** ~$80-120

---

## Phase 4: Data Verification

### 4.1 Check Completeness
```bash
# Count conversations
ls outputs/exp_*.json | wc -l

# Should see 2 files (one per variant) for main study
# Each file contains all persona×scenario combinations
```

### 4.2 Verify Data Quality
```python
import json
import glob

# Load results
files = glob.glob('outputs/exp_*_main_study_*.json')
for f in files:
    with open(f) as file:
        data = json.load(file)
        print(f"\n{data['variant']} - {data['experiment_name']}")
        print(f"Total conversations: {data['summary']['total_conversations']}")
        print(f"Success rate: {data['summary']['successful_conversations']}")
        print(f"Avg empathy: {data['summary']['avg_empathy']:.3f}")
        print(f"Avg clarity: {data['summary']['avg_clarity']:.3f}")
        print(f"Avg task success: {data['summary']['avg_task_success']:.3f}")
```

### 4.3 Quality Checks
- [ ] All conversations completed (no crashes)
- [ ] Evaluation scores in valid range (0.0-1.0)
- [ ] Conversations have reasonable length (not all 1 turn or max turns)
- [ ] Different personas show different behaviors
- [ ] Variant A and B show measurable differences

---

## Phase 5: Database Cleanup (Optional)

Since simulated data goes to your database with `sim_` prefix:

```sql
-- Check how much test data you have
SELECT
  COUNT(DISTINCT CASE WHEN session_id LIKE 'sim_%' THEN session_id END) as test_sessions,
  COUNT(DISTINCT CASE WHEN session_id NOT LIKE 'sim_%' THEN session_id END) as real_sessions
FROM messages;

-- Optional: Delete test data after collection (if needed)
-- DELETE FROM messages WHERE session_id LIKE 'sim_%';
```

---

## Timeline Suggestion

**Day 1:**
- Morning: Setup & pre-flight test (30 min)
- Afternoon: Pilot study (1 hour)
- Evening: Review pilot, adjust if needed

**Day 2:**
- Morning: Main data collection Variant A (1.5-2 hours)
- Afternoon: Main data collection Variant B (1.5-2 hours)
- Evening: Verify data quality

**Day 3:**
- Analysis and dissertation writing

---

## Troubleshooting

### "OpenAI API key invalid"
- Check .env file has correct key
- Ensure no extra spaces or quotes

### "Failed to connect to API"
- Verify VodaCare server is running: `curl http://localhost:8000/health`
- Check server logs for errors

### "Conversations too short"
- Check termination logic in logs
- May need to adjust persona patience thresholds

### "Scores all similar"
- Check LLM judge prompts are working
- Review rationale in output JSON
- May need to adjust evaluation rubric

### High costs
- Start with pilot (15 conversations)
- Use `--dry-run` to preview without running
- Monitor OpenAI API dashboard

---

## Quick Reference Commands

```bash
# Activate environment
source venv/bin/activate

# List available options
python3 run_experiment.py --list-personas
python3 run_experiment.py --list-scenarios

# Preview without running
python3 run_experiment.py --variant A --personas persona_01 --scenarios scenario_001 --dry-run

# Single test
python3 run_experiment.py --variant A --personas persona_01 --scenarios scenario_001 --name "test"

# View logs
tail -f experiment.log

# View summary
cat outputs/summary_*.json | jq '.summary'
```

---

## Data Files You'll Collect

After main study, you'll have:

1. **Full experiment files**: `exp_A_main_study_*.json` and `exp_B_main_study_*.json`
   - Complete transcripts
   - Turn-by-turn conversations
   - Evaluation scores with rationale
   - Heuristic check results

2. **Summary files**: `summary_A_main_study_*.json` and `summary_B_main_study_*.json`
   - Aggregated statistics
   - Success rates
   - Average scores by dimension
   - Scores by persona and scenario

3. **Log file**: `experiment.log`
   - Detailed execution trace
   - Error messages
   - Debugging information

---

## Next: Analysis

Once you have the data, you'll:
1. Load JSON files into pandas/R
2. Compare empathy scores between variants
3. Check for interaction effects (variant × scenario)
4. Create visualizations
5. Run statistical tests (t-test, ANOVA)

Would you like me to create analysis scripts for after collection?
