# Evaluating Real User Conversations

To compare real users and simulated users fairly, you need to evaluate both through the **same evaluation pipeline** (LLM judge + heuristics).

## Workflow

```
Real User Data (Supabase)
    → Export to CSV
    → Evaluate with same pipeline
    → Compare with simulated results
```

---

## Step 1: Export Real User Data from Database

```bash
cd /Users/stagcto/fyp/llm-testing
source venv/bin/activate

# Export real conversations (excludes sim_ sessions)
python3 export_real_users.py --output data/real_conversations.csv
```

**This will:**
- Connect to your Supabase database
- Fetch all messages where `session_id` does NOT start with `sim_`
- Export to CSV with format: `session_id, participant_id, participant_group, role, content, created_at`

**Output:**
```
Fetched 1234 messages
Filtered to 856 real user messages
✓ Exported 856 messages to data/real_conversations.csv
✓ 142 unique sessions

Variant breakdown:
  A: 423 messages
  B: 433 messages
```

---

## Step 2: Evaluate Real Users with Same Pipeline

```bash
# Evaluate using same LLM judge and heuristics
python3 evaluate_real_users.py \
  --csv data/real_conversations.csv \
  --output outputs/real_user_evaluation.json
```

**This will:**
- Load conversations from CSV
- Group messages by session_id
- Run each through:
  - **LLM Judge** (GPT-4) - scores on same 4 dimensions
  - **Heuristic Checks** - same safety validations
- Produce same format output as simulated runs

**Output:**
```
================================================================================
REAL USER EVALUATION SUMMARY
================================================================================
Total conversations: 142
Successful (task_success >= 0.7): 98

AVERAGE SCORES
  Task Success: 0.78
  Clarity: 0.82
  Empathy: 0.71
  Policy Compliance: 0.94
  Overall Weighted: 0.79

HEURISTIC CHECKS
  Pass rate: 94.4%
  Critical failures: 5.6%
================================================================================
```

---

## Step 3: Compare Real vs Simulated

Now you have comparable data:

```python
import json

# Load simulated results
with open('outputs/exp_A_main_study_*.json') as f:
    sim_data = json.load(f)

# Load real user results
with open('outputs/real_user_evaluation.json') as f:
    real_data = json.load(f)

# Compare
print("SIMULATED USERS:")
print(f"  Avg Empathy: {sim_data['summary']['avg_empathy']:.3f}")
print(f"  Avg Task Success: {sim_data['summary']['avg_task_success']:.3f}")

print("\nREAL USERS:")
print(f"  Avg Empathy: {real_data['summary']['avg_empathy']:.3f}")
print(f"  Avg Task Success: {real_data['summary']['avg_task_success']:.3f}")
```

---

## CSV Format

The export creates a CSV with these columns:

```csv
session_id,participant_id,participant_group,role,content,created_at
sess_abc123,user_001,A,user,"I need help with my bill",2026-01-28T10:30:00
sess_abc123,user_001,A,assistant,"I'd be happy to help...",2026-01-28T10:30:15
sess_abc123,user_001,A,user,"When will I be charged?",2026-01-28T10:31:00
...
```

**Key columns:**
- `session_id`: Groups messages into conversations
- `participant_group`: Variant (A or B) for comparison
- `role`: "user" or "assistant"
- `content`: Message text
- `created_at`: Timestamp for ordering

---

## Evaluation Pipeline

Both real and simulated users go through:

### 1. LLM Judge (GPT-4)
Evaluates on 4 dimensions (0.0-1.0):
- **Task Success (50%)**: Did conversation achieve goal?
- **Clarity (20%)**: Clear and understandable?
- **Empathy (20%)**: Appropriate tone?
- **Policy Compliance (10%)**: No violations?

### 2. Heuristic Checks
Deterministic safety checks:
- No hallucinated plans (validates against catalog)
- No contradictions
- Appropriate response length
- Escalation when needed

### 3. Summary Statistics
Aggregates across all conversations:
- Average scores per dimension
- Success rates
- Heuristic pass rates
- Breakdown by variant

---

## Analysis: Real vs Simulated

### Question 1: Are simulated users realistic?

Compare distributions:

```python
import matplotlib.pyplot as plt

# Plot score distributions
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

dimensions = ['avg_empathy', 'avg_clarity', 'avg_task_success', 'avg_policy_compliance']
titles = ['Empathy', 'Clarity', 'Task Success', 'Policy Compliance']

for ax, dim, title in zip(axes.flat, dimensions, titles):
    ax.bar(['Simulated', 'Real'],
           [sim_data['summary'][dim], real_data['summary'][dim]])
    ax.set_ylabel('Score')
    ax.set_title(title)
    ax.set_ylim(0, 1)

plt.tight_layout()
plt.savefig('real_vs_simulated_comparison.png')
```

**If distributions are similar:** Simulated users are realistic ✓

**If very different:** May need to adjust persona definitions

### Question 2: Does system prompt effect hold for real users?

Compare Variant A vs B for both:

```python
# Simulated users
sim_a = json.load(open('outputs/exp_A_main_study_*.json'))
sim_b = json.load(open('outputs/exp_B_main_study_*.json'))

# Real users (split by variant)
real_a_convos = [c for c in real_data['conversations'] if c['variant'] == 'A']
real_b_convos = [c for c in real_data['conversations'] if c['variant'] == 'B']

real_a_empathy = sum(c['llm_evaluation']['empathy'] for c in real_a_convos) / len(real_a_convos)
real_b_empathy = sum(c['llm_evaluation']['empathy'] for c in real_b_convos) / len(real_b_convos)

print("EMPATHY SCORES:")
print(f"Simulated A: {sim_a['summary']['avg_empathy']:.3f}")
print(f"Simulated B: {sim_b['summary']['avg_empathy']:.3f}")
print(f"Real A: {real_a_empathy:.3f}")
print(f"Real B: {real_b_empathy:.3f}")
```

**For your dissertation:**
- If both show A > B on empathy: Strong evidence for system prompt effect
- If only simulated shows effect: May indicate limitation of simulation
- If real users show BIGGER effect: Simulated users may underestimate impact

---

## Important Notes

### Database Filtering
- Simulated sessions: `session_id LIKE 'sim_%'`
- Real users: `session_id NOT LIKE 'sim_%'`

Ensure your real users don't accidentally have `sim_` prefix!

### Evaluation Costs
- Real user evaluation uses GPT-4 for judging
- Cost: ~$0.50 per conversation
- 142 real conversations ≈ $70

Budget accordingly!

### Missing Context
Real user conversations don't have:
- Persona definitions (age, tech literacy, etc.)
- Scenario goals (what they're trying to achieve)

The evaluator uses **placeholders** for these, judging purely on transcript quality.

---

## Troubleshooting

### "No real user messages found"
Check your database:
```sql
SELECT COUNT(*)
FROM messages
WHERE session_id NOT LIKE 'sim_%';
```

If zero, you haven't collected real user data yet.

### "Supabase not configured"
Set environment variables:
```bash
export SUPABASE_URL="your_supabase_url"
export SUPABASE_SERVICE_KEY="your_service_key"
```

Or add to `/Users/stagcto/fyp/server/.env`

### Export fails with errors
Check server .env has correct Supabase credentials:
```bash
cd /Users/stagcto/fyp/server
cat .env | grep SUPABASE
```

---

## Full Workflow Example

```bash
# 1. Export real user data
python3 export_real_users.py --output data/real_conversations.csv

# 2. Evaluate real users
python3 evaluate_real_users.py \
  --csv data/real_conversations.csv \
  --output outputs/real_user_evaluation.json

# 3. Compare with simulated
python3 -c "
import json

sim = json.load(open('outputs/exp_A_main_study_*.json'))
real = json.load(open('outputs/real_user_evaluation.json'))

print('=== COMPARISON ===')
print(f'Simulated empathy: {sim[\"summary\"][\"avg_empathy\"]:.3f}')
print(f'Real empathy: {real[\"summary\"][\"avg_empathy\"]:.3f}')
print(f'Difference: {abs(sim[\"summary\"][\"avg_empathy\"] - real[\"summary\"][\"avg_empathy\"]):.3f}')
"
```

---

## For Your Dissertation

This allows you to make claims like:

> "Both simulated and real users were evaluated using identical criteria:
> a GPT-4-based judge scoring on task success (50%), clarity (20%),
> empathy (20%), and policy compliance (10%), plus deterministic heuristic
> checks. This ensures fair comparison between experimental conditions."

And:

> "The system prompt effect observed in simulated users (Δempathy = 0.15)
> was validated against real user data (Δempathy = 0.12), demonstrating
> the simulation's ecological validity."

This strengthens your methodology significantly! 🎓
