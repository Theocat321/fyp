# Data Collection Run Tracker

Track your progress through all persona × scenario combinations.

## Full Study Design

**Total Combinations:** 60 conversations (10 personas × 3 scenarios × 2 variants)

---

## Selected Personas (10)

- ✅ persona_01_frustrated_commuter (angry, moderate tech)
- ✅ persona_02_elderly_tech_newbie (polite, low tech)
- ✅ persona_03_teen_gamer (casual, high tech)
- ✅ persona_06_student_budgeter (skeptical, questions everything)
- ✅ persona_08_family_organizer (chatty, friendly)
- ✅ persona_09_rude_rage_quitter (aggressive, caps lock)
- ✅ persona_12_accessibility_user (blind, precise needs)
- ✅ persona_17_bargain_hunter (strategic negotiator)
- ✅ persona_18_loyal_longtime_customer (emotional appeal)
- ✅ persona_19_fraud_victim (panicked, urgent)

## Selected Scenarios (3)

- ✅ scenario_001_esim_setup (technical, straightforward)
- ✅ scenario_003_billing_dispute (emotional, complex)
- ✅ scenario_005_network_issue (troubleshooting, systematic)

---

## Batch Run Commands

### Option 1: Run All At Once (Recommended)

```bash
cd /Users/stagcto/fyp/llm-testing
source venv/bin/activate

# All Variant A (30 conversations, ~1 hour, ~$15)
python3 run_experiment.py \
  --variant A \
  --personas persona_01,persona_02,persona_03,persona_06,persona_08,persona_09,persona_12,persona_17,persona_18,persona_19 \
  --scenarios scenario_001,scenario_003,scenario_005 \
  --name "main_study_a" \
  | tee logs/run_variant_a.log

# All Variant B (30 conversations, ~1 hour, ~$15)
python3 run_experiment.py \
  --variant B \
  --personas persona_01,persona_02,persona_03,persona_06,persona_08,persona_09,persona_12,persona_17,persona_18,persona_19 \
  --scenarios scenario_001,scenario_003,scenario_005 \
  --name "main_study_b" \
  | tee logs/run_variant_b.log
```

---

## Option 2: Run By Scenario (Break into smaller chunks)

### Batch 1: eSIM Setup (10 conversations per variant)

```bash
# Variant A - eSIM
python3 run_experiment.py \
  --variant A \
  --personas persona_01,persona_02,persona_03,persona_06,persona_08,persona_09,persona_12,persona_17,persona_18,persona_19 \
  --scenarios scenario_001 \
  --name "batch1_esim_a"

# Variant B - eSIM
python3 run_experiment.py \
  --variant B \
  --personas persona_01,persona_02,persona_03,persona_06,persona_08,persona_09,persona_12,persona_17,persona_18,persona_19 \
  --scenarios scenario_001 \
  --name "batch1_esim_b"
```

**Progress:** [  ] Batch 1 Complete
- [ ] Variant A - scenario_001
- [ ] Variant B - scenario_001

---

### Batch 2: Billing Dispute (10 conversations per variant)

```bash
# Variant A - Billing
python3 run_experiment.py \
  --variant A \
  --personas persona_01,persona_02,persona_03,persona_06,persona_08,persona_09,persona_12,persona_17,persona_18,persona_19 \
  --scenarios scenario_003 \
  --name "batch2_billing_a"

# Variant B - Billing
python3 run_experiment.py \
  --variant B \
  --personas persona_01,persona_02,persona_03,persona_06,persona_08,persona_09,persona_12,persona_17,persona_18,persona_19 \
  --scenarios scenario_003 \
  --name "batch2_billing_b"
```

**Progress:** [  ] Batch 2 Complete
- [ ] Variant A - scenario_003
- [ ] Variant B - scenario_003

---

### Batch 3: Network Issue (10 conversations per variant)

```bash
# Variant A - Network
python3 run_experiment.py \
  --variant A \
  --personas persona_01,persona_02,persona_03,persona_06,persona_08,persona_09,persona_12,persona_17,persona_18,persona_19 \
  --scenarios scenario_005 \
  --name "batch3_network_a"

# Variant B - Network
python3 run_experiment.py \
  --variant B \
  --personas persona_01,persona_02,persona_03,persona_06,persona_08,persona_09,persona_12,persona_17,persona_18,persona_19 \
  --scenarios scenario_005 \
  --name "batch3_network_b"
```

**Progress:** [  ] Batch 3 Complete
- [ ] Variant A - scenario_005
- [ ] Variant B - scenario_005

---

## Option 3: Run Individual Combinations (Maximum Control)

Use this if you want to run specific persona-scenario pairs one at a time.

### Template
```bash
python3 run_experiment.py \
  --variant [A or B] \
  --personas [single_persona_id] \
  --scenarios [single_scenario_id] \
  --name "[descriptive_name]"
```

### Individual Run Checklist

#### Scenario 001: eSIM Setup

**Variant A:**
- [ ] persona_01 + scenario_001: `--name "p01_s001_a"`
- [ ] persona_02 + scenario_001: `--name "p02_s001_a"`
- [ ] persona_03 + scenario_001: `--name "p03_s001_a"`
- [ ] persona_06 + scenario_001: `--name "p06_s001_a"`
- [ ] persona_08 + scenario_001: `--name "p08_s001_a"`
- [ ] persona_09 + scenario_001: `--name "p09_s001_a"`
- [ ] persona_12 + scenario_001: `--name "p12_s001_a"`
- [ ] persona_17 + scenario_001: `--name "p17_s001_a"`
- [ ] persona_18 + scenario_001: `--name "p18_s001_a"`
- [ ] persona_19 + scenario_001: `--name "p19_s001_a"`

**Variant B:**
- [ ] persona_01 + scenario_001: `--name "p01_s001_b"`
- [ ] persona_02 + scenario_001: `--name "p02_s001_b"`
- [ ] persona_03 + scenario_001: `--name "p03_s001_b"`
- [ ] persona_06 + scenario_001: `--name "p06_s001_b"`
- [ ] persona_08 + scenario_001: `--name "p08_s001_b"`
- [ ] persona_09 + scenario_001: `--name "p09_s001_b"`
- [ ] persona_12 + scenario_001: `--name "p12_s001_b"`
- [ ] persona_17 + scenario_001: `--name "p17_s001_b"`
- [ ] persona_18 + scenario_001: `--name "p18_s001_b"`
- [ ] persona_19 + scenario_001: `--name "p19_s001_b"`

#### Scenario 003: Billing Dispute

**Variant A:**
- [ ] persona_01 + scenario_003: `--name "p01_s003_a"`
- [ ] persona_02 + scenario_003: `--name "p02_s003_a"`
- [ ] persona_03 + scenario_003: `--name "p03_s003_a"`
- [ ] persona_06 + scenario_003: `--name "p06_s003_a"`
- [ ] persona_08 + scenario_003: `--name "p08_s003_a"`
- [ ] persona_09 + scenario_003: `--name "p09_s003_a"`
- [ ] persona_12 + scenario_003: `--name "p12_s003_a"`
- [ ] persona_17 + scenario_003: `--name "p17_s003_a"`
- [ ] persona_18 + scenario_003: `--name "p18_s003_a"`
- [ ] persona_19 + scenario_003: `--name "p19_s003_a"`

**Variant B:**
- [ ] persona_01 + scenario_003: `--name "p01_s003_b"`
- [ ] persona_02 + scenario_003: `--name "p02_s003_b"`
- [ ] persona_03 + scenario_003: `--name "p03_s003_b"`
- [ ] persona_06 + scenario_003: `--name "p06_s003_b"`
- [ ] persona_08 + scenario_003: `--name "p08_s003_b"`
- [ ] persona_09 + scenario_003: `--name "p09_s003_b"`
- [ ] persona_12 + scenario_003: `--name "p12_s003_b"`
- [ ] persona_17 + scenario_003: `--name "p17_s003_b"`
- [ ] persona_18 + scenario_003: `--name "p18_s003_b"`
- [ ] persona_19 + scenario_003: `--name "p19_s003_b"`

#### Scenario 005: Network Issue

**Variant A:**
- [ ] persona_01 + scenario_005: `--name "p01_s005_a"`
- [ ] persona_02 + scenario_005: `--name "p02_s005_a"`
- [ ] persona_03 + scenario_005: `--name "p03_s005_a"`
- [ ] persona_06 + scenario_005: `--name "p06_s005_a"`
- [ ] persona_08 + scenario_005: `--name "p08_s005_a"`
- [ ] persona_09 + scenario_005: `--name "p09_s005_a"`
- [ ] persona_12 + scenario_005: `--name "p12_s005_a"`
- [ ] persona_17 + scenario_005: `--name "p17_s005_a"`
- [ ] persona_18 + scenario_005: `--name "p18_s005_a"`
- [ ] persona_19 + scenario_005: `--name "p19_s005_a"`

**Variant B:**
- [ ] persona_01 + scenario_005: `--name "p01_s005_b"`
- [ ] persona_02 + scenario_005: `--name "p02_s005_b"`
- [ ] persona_03 + scenario_005: `--name "p03_s005_b"`
- [ ] persona_06 + scenario_005: `--name "p06_s005_b"`
- [ ] persona_08 + scenario_005: `--name "p08_s005_b"`
- [ ] persona_09 + scenario_005: `--name "p09_s005_b"`
- [ ] persona_12 + scenario_005: `--name "p12_s005_b"`
- [ ] persona_17 + scenario_005: `--name "p17_s005_b"`
- [ ] persona_18 + scenario_005: `--name "p18_s005_b"`
- [ ] persona_19 + scenario_005: `--name "p19_s005_b"`

---

## Progress Tracking

### Overall Progress
```
Total: 60 conversations
Completed: ___ / 60
Remaining: ___

Variant A: ___ / 30
Variant B: ___ / 30
```

### Check Completed Runs
```bash
# Count output files
ls outputs/exp_*.json | wc -l

# List all completed runs
ls -1 outputs/exp_*.json | grep -o 'exp_[AB]_[^_]*' | sort

# Check specific combination exists
ls outputs/exp_A_*main_study*.json 2>/dev/null && echo "✓ Main Study A complete" || echo "✗ Not found"
ls outputs/exp_B_*main_study*.json 2>/dev/null && echo "✓ Main Study B complete" || echo "✗ Not found"
```

---

## Merging Results (If running in batches)

If you ran in batches (option 2 or 3), you can merge results for analysis:

```python
import json
import glob

# Collect all variant A files
a_files = glob.glob('outputs/exp_A_*.json')
all_a_conversations = []
for f in a_files:
    with open(f) as file:
        data = json.load(file)
        all_a_conversations.extend(data['conversations'])

print(f"Total Variant A conversations: {len(all_a_conversations)}")

# Same for variant B
b_files = glob.glob('outputs/exp_B_*.json')
all_b_conversations = []
for f in b_files:
    with open(f) as file:
        data = json.load(file)
        all_b_conversations.extend(data['conversations'])

print(f"Total Variant B conversations: {len(all_b_conversations)}")
```

---

## Data Quality Checks

After each batch:

```bash
# View latest summary
ls -t outputs/summary_*.json | head -1 | xargs cat | jq '.summary'

# Check for errors
grep -i error experiment.log | tail -20

# Verify conversation count
cat outputs/exp_*_[last_run]*.json | jq '.summary.total_conversations'
```

---

## Estimated Time & Cost

| Option | Conversations | Time | Cost |
|--------|--------------|------|------|
| Smoke Test | 6 | 15 min | $3-5 |
| Single Batch | 20 | 30 min | $10-15 |
| Full Study (Option 1) | 60 | 2 hours | $30-40 |
| By Scenario (Option 2) | 60 | 2 hours | $30-40 |
| Individual (Option 3) | 60 | 2-3 hours | $30-40 |

---

## Backup & Version Control

After each successful batch:

```bash
# Create timestamped backup
cp -r outputs outputs_backup_$(date +%Y%m%d_%H%M%S)

# Or git commit if using version control
git add outputs/
git commit -m "Data collection batch completed: $(date)"
```
