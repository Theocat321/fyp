# Running the Full Experiment - Complete Guide

**Goal:** Collect 60 conversations (10 personas × 3 scenarios × 2 variants) for your dissertation analysis.

**Time:** ~2-2.5 hours total
**Cost:** ~$30-40 USD (OpenAI API)
**Difficulty:** Easy - just run 2 commands and wait

---

## Prerequisites Checklist

Before starting, verify these are complete:

```bash
cd /Users/stagcto/fyp/llm-testing

# 1. Virtual environment activated
source venv/bin/activate

# 2. Check .env has real OpenAI API key
cat .env | grep OPENAI_API_KEY
# Should show: OPENAI_API_KEY=sk-proj-...

# 3. VodaCare server is running (in separate terminal)
curl http://localhost:8000/health
# Should return: {"status":"ok",...}

# 4. Smoke test files exist (confirms previous tests worked)
ls outputs/*smoke_test*.json
# Should show 4 files (exp and summary for A and B)
```

**If any check fails, see Troubleshooting section at bottom.**

---

## Step 1: Run Variant A (30 conversations)

Open your terminal in the llm-testing directory:

```bash
cd /Users/stagcto/fyp/llm-testing
source venv/bin/activate

python3 run_experiment.py \
--variant A \
--personas persona_01_frustrated_commuter,persona_02_elderly_tech_newbie,persona_03_teen_gamer,persona_06_student_budgeter,persona_08_family_organizer,persona_09_rude_rage_quitter,persona_12_accessibility_user,persona_17_bargain_hunter,persona_18_loyal_longtime_customer,persona_19_fraud_victim \
--scenarios scenario_001_esim_setup,scenario_003_billing_dispute,scenario_005_network_issue \
--name "dissertation_variant_a"
```

### What You'll See

```
2026-01-28 18:15:00 - INFO - Starting Experiment: dissertation_variant_a
2026-01-28 18:15:00 - INFO - Experiment ID: exp_20260128_181500_abc123
2026-01-28 18:15:00 - INFO - Variant: A
2026-01-28 18:15:00 - INFO - Personas: 10
2026-01-28 18:15:00 - INFO - Scenarios: 3
2026-01-28 18:15:00 - INFO - Total conversations: 30
================================================================================

[1/30] Running: persona_01_frustrated_commuter × scenario_001_esim_setup
--- Turn 1 ---
User: [persona message]
Assistant: [response]
--- Turn 2 ---
...
✓ Completed: 4 turns, score: 0.720, reason: satisfaction

[2/30] Running: persona_01_frustrated_commuter × scenario_003_billing_dispute
...
```

### Progress Tracking

The experiment will show:
- `[X/30]` - Current conversation number
- Turn-by-turn dialogue
- Completion status with score
- Estimated time remaining (not shown but ~2-4 min per conversation)

**Let it run!** Don't interrupt or close the terminal.

### Expected Duration

- **Per conversation:** 2-4 minutes (depends on conversation length)
- **30 conversations:** 60-120 minutes (~1-2 hours)
- **Faster with shorter conversations** (escalations end quickly)

### When Complete

You'll see:

```
================================================================================
EXPERIMENT SUMMARY
================================================================================
Experiment: dissertation_variant_a
Variant: A
Duration: 89.3m

CONVERSATIONS
  Total: 30
  Successful (task_success >= 0.7): 22
  Success rate: 73.3%

AVERAGE SCORES
  Task Success: 0.762
  Clarity: 0.831
  Empathy: 0.895
  Policy Compliance: 0.943
  Overall Weighted: 0.823

...

Results written to:
  Full: outputs/exp_A_dissertation_variant_a_20260128_192345.json
  Summary: outputs/summary_A_dissertation_variant_a_20260128_192345.json

Experiment completed successfully
```

**✓ Checkpoint:** Files created successfully

---

## Step 2: Run Variant B (30 conversations)

**After Variant A completes**, run the same command with `--variant B`:

```bash
python3 run_experiment.py \
--variant B \
--personas persona_01_frustrated_commuter,persona_02_elderly_tech_newbie,persona_03_teen_gamer,persona_06_student_budgeter,persona_08_family_organizer,persona_09_rude_rage_quitter,persona_12_accessibility_user,persona_17_bargain_hunter,persona_18_loyal_longtime_customer,persona_19_fraud_victim \
--scenarios scenario_001_esim_setup,scenario_003_billing_dispute,scenario_005_network_issue \
--name "dissertation_variant_b"
```

Same process as above - let it run for ~1-2 hours.

**When complete, you'll have all 60 conversations!**

---

## Step 3: Verify Your Data

After both runs complete:

```bash
# Check files were created
ls outputs/exp_*_dissertation_*.json
# Should show 2 files:
# - exp_A_dissertation_variant_a_[timestamp].json
# - exp_B_dissertation_variant_b_[timestamp].json

ls outputs/summary_*_dissertation_*.json
# Should show 2 files:
# - summary_A_dissertation_variant_a_[timestamp].json
# - summary_B_dissertation_variant_b_[timestamp].json

# Quick view of results
cat outputs/summary_A_dissertation_*.json | jq '.summary | {
  total: .total_conversations,
  empathy_a: .avg_empathy,
  clarity_a: .avg_clarity,
  task_success_a: .avg_task_success
}'

cat outputs/summary_B_dissertation_*.json | jq '.summary | {
  total: .total_conversations,
  empathy_b: .avg_empathy,
  clarity_b: .avg_clarity,
  task_success_b: .avg_task_success
}'
```

**Expected output:**
- Each file has 30 conversations
- Scores are in 0.0-1.0 range
- Variant A likely has higher empathy than B

---

## Step 4: Backup Your Data

**IMPORTANT:** Back up immediately before doing anything else:

```bash
# Create timestamped backup
cp -r outputs outputs_backup_$(date +%Y%m%d_%H%M%S)

# Verify backup
ls -lh outputs_backup_*/

# Optional: Commit to git if using version control
git add outputs/
git commit -m "Data collection complete: 60 conversations for dissertation"
```

---

## What You Now Have

### Files Created

```
outputs/
├── exp_A_dissertation_variant_a_[timestamp].json     (Full data - Variant A)
├── exp_B_dissertation_variant_b_[timestamp].json     (Full data - Variant B)
├── summary_A_dissertation_variant_a_[timestamp].json (Summary - Variant A)
└── summary_B_dissertation_variant_b_[timestamp].json (Summary - Variant B)
```

### Database Records

Your Supabase database now contains:
- **60 participants** (participant_id: `llm_test_43` through `llm_test_102`)
- **~360-600 messages** (depends on conversation length)
- All tagged with `sim_` prefix in session_id

To verify:

```sql
-- Check message count
SELECT
  COUNT(*) as total_messages,
  COUNT(DISTINCT session_id) as conversations
FROM messages
WHERE session_id LIKE 'sim_persona%';

-- Should show ~60 conversations, ~400-600 messages
```

---

## Quick Analysis (Optional)

Compare the two variants:

```bash
# Create comparison script
cat > compare_variants.py << 'EOF'
import json
import glob

# Find the files
a_file = glob.glob('outputs/summary_A_dissertation_*.json')[0]
b_file = glob.glob('outputs/summary_B_dissertation_*.json')[0]

with open(a_file) as f:
    variant_a = json.load(f)

with open(b_file) as f:
    variant_b = json.load(f)

print("="*60)
print("VARIANT COMPARISON")
print("="*60)

dimensions = ['avg_empathy', 'avg_clarity', 'avg_task_success', 'avg_overall_score']
labels = ['Empathy', 'Clarity', 'Task Success', 'Overall']

for dim, label in zip(dimensions, labels):
    a_score = variant_a['summary'][dim]
    b_score = variant_b['summary'][dim]
    diff = a_score - b_score
    winner = "A" if diff > 0 else "B" if diff < 0 else "Tie"

    print(f"\n{label}:")
    print(f"  Variant A: {a_score:.3f}")
    print(f"  Variant B: {b_score:.3f}")
    print(f"  Difference: {diff:+.3f} (Winner: {winner})")

print("\n" + "="*60)
EOF

# Run comparison
python3 compare_variants.py
```

**Expected output:**
```
============================================================
VARIANT COMPARISON
============================================================

Empathy:
  Variant A: 0.892
  Variant B: 0.541
  Difference: +0.351 (Winner: A)

Clarity:
  Variant A: 0.823
  Variant B: 0.789
  Difference: +0.034 (Winner: A)

Task Success:
  Variant A: 0.762
  Variant B: 0.758
  Difference: +0.004 (Winner: A)

Overall:
  Variant A: 0.823
  Variant B: 0.715
  Difference: +0.108 (Winner: A)
============================================================
```

---

## Cost Breakdown

### API Calls Made

**Per conversation:**
- User simulator: 4-8 calls (depends on turns) @ $0.02 each
- LLM judge: 1 call @ $0.30 each
- VodaCare assistant: 4-8 calls (through your backend)

**Total for 60 conversations:**
- ~300 simulator calls: $6
- 60 judge calls: $18
- ~300 assistant calls: $6
- **Total: ~$30-40**

### Verify Cost

Check your OpenAI dashboard:
https://platform.openai.com/usage

You should see increased usage on the day you ran experiments.

---

## Next Steps

After data collection:

### 1. Statistical Analysis

See `ANALYSIS_GUIDE.md` (if created) or use Python/R to:
- Run t-tests comparing variants
- Calculate effect sizes (Cohen's d)
- Test for interaction effects (persona × variant)
- Create visualizations

### 2. Export Real User Data (For Comparison)

```bash
# Export real users from database
python3 export_real_users.py --output data/real_conversations.csv

# Evaluate with same pipeline
python3 evaluate_real_users.py \
  --csv data/real_conversations.csv \
  --output outputs/real_user_evaluation.json

# Now compare simulated vs real
```

### 3. Write Dissertation

You now have:
- ✓ 60 simulated conversations
- ✓ Evaluation scores for 4 dimensions
- ✓ Breakdown by persona and scenario
- ✓ Statistical comparison between variants
- ✓ (Optional) Real user comparison

---

## Troubleshooting

### Error: "OPENAI_API_KEY must be set"

```bash
# Check .env file
cat .env | grep OPENAI_API_KEY

# If empty, edit .env:
nano .env
# Add: OPENAI_API_KEY=sk-proj-your-actual-key
```

### Error: "Failed to connect to API at http://localhost:8000"

```bash
# Start VodaCare server in separate terminal
cd /Users/stagcto/fyp/server
source venv/bin/activate
uvicorn app.main:app --reload

# Verify it's running
curl http://localhost:8000/health
```

### Error: "No module named 'src'"

```bash
# Make sure you're in llm-testing directory
pwd
# Should show: /Users/stagcto/fyp/llm-testing

# Activate virtual environment
source venv/bin/activate
```

### Experiment crashes mid-run

Check `experiment.log`:
```bash
tail -50 experiment.log
```

Common issues:
- OpenAI rate limits → Wait 60 seconds, resume from where it crashed
- Network issues → Check internet connection
- Out of API credits → Add more credits to OpenAI account

### Want to resume from partial run

The experiment runner doesn't checkpoint by default, so you'd need to:

```bash
# If crashed at conversation 15/30
# Adjust personas to skip completed ones
# Check outputs/ to see which persona×scenario combos completed
ls outputs/exp_A_dissertation_*.json

# Extract which ran:
cat outputs/exp_A_dissertation_*.json | jq '.conversations[] | {persona: .persona_id, scenario: .scenario_id}'

# Re-run with remaining personas only
```

### Scores seem wrong

Check a few transcripts manually:
```bash
# View one conversation
cat outputs/exp_A_dissertation_*.json | jq '.conversations[0]' | less

# Look at:
# - Is conversation realistic?
# - Are scores reasonable given transcript?
# - Is evaluation rationale sensible?
```

If scores are consistently off, may need to adjust evaluation rubric.

---

## Important Notes

### Don't Interrupt
- Let each variant run to completion
- Interrupting (Ctrl+C) will lose progress
- Each run takes 1-2 hours - plan accordingly

### Monitor Progress
```bash
# In another terminal, watch logs
tail -f experiment.log

# Count completed conversations
cat outputs/exp_A_dissertation_*.json 2>/dev/null | jq '.conversations | length'
```

### API Rate Limits

If you hit OpenAI rate limits:
1. Wait 60 seconds
2. The script will retry automatically
3. If it crashes, you'll need to rerun

### Database Storage

All conversations are stored in Supabase. If you want to keep database clean:
```sql
-- After experiments, optionally delete test data
DELETE FROM messages WHERE session_id LIKE 'sim_%';
DELETE FROM participants WHERE participant_id LIKE 'llm_test_%';
```

But keep it for now - useful for verification!

---

## Timeline

### Day 1: Data Collection
- **Morning:** Run Variant A (1-2 hours)
- **Afternoon:** Run Variant B (1-2 hours)
- **Evening:** Backup data, run quick comparison

### Day 2: Analysis
- Export real user data
- Evaluate real users
- Run statistical tests
- Create visualizations

### Day 3+: Writing
- Draft methodology section
- Write results section
- Create tables and figures
- Discussion and conclusions

---

## Success Criteria

Your data collection is successful if:

- [x] 2 experiment files created (A and B)
- [x] Each has 30 conversations
- [x] All scores in 0.0-1.0 range
- [x] Variant A has higher empathy than B
- [x] No critical heuristic failures
- [x] Conversations look realistic
- [x] Files backed up safely

---

## Good Luck! 🎓

You're now ready to collect dissertation-quality data. The experiment is fully automated - just run the two commands and wait.

**Questions?** Check:
- `DATA_PIPELINES.md` - How everything works
- `SMOKE_TEST_COMPARISON.md` - What to expect from results
- `REAL_USER_EVALUATION.md` - How to compare with real users
- `experiment.log` - Detailed logs if something goes wrong

**When you return:**
1. Check both files exist in `outputs/`
2. Run the comparison script
3. Back up your data
4. Start analysis!

---

## Quick Commands Reference

```bash
# Start VodaCare server (separate terminal)
cd /Users/stagcto/fyp/server && source venv/bin/activate && uvicorn app.main:app --reload

# Run Variant A
cd /Users/stagcto/fyp/llm-testing && source venv/bin/activate && python3 run_experiment.py --variant A --personas persona_01_frustrated_commuter,persona_02_elderly_tech_newbie,persona_03_teen_gamer,persona_06_student_budgeter,persona_08_family_organizer,persona_09_rude_rage_quitter,persona_12_accessibility_user,persona_17_bargain_hunter,persona_18_loyal_longtime_customer,persona_19_fraud_victim --scenarios scenario_001_esim_setup,scenario_003_billing_dispute,scenario_005_network_issue --name "dissertation_variant_a"

# Run Variant B
python3 run_experiment.py --variant B --personas persona_01_frustrated_commuter,persona_02_elderly_tech_newbie,persona_03_teen_gamer,persona_06_student_budgeter,persona_08_family_organizer,persona_09_rude_rage_quitter,persona_12_accessibility_user,persona_17_bargain_hunter,persona_18_loyal_longtime_customer,persona_19_fraud_victim --scenarios scenario_001_esim_setup,scenario_003_billing_dispute,scenario_005_network_issue --name "dissertation_variant_b"

# Backup
cp -r outputs outputs_backup_$(date +%Y%m%d_%H%M%S)

# Compare
python3 compare_variants.py
```
