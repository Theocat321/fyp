# Database Impact: Simulated vs Real Users

## Yes, Simulated Conversations ARE Saved to Database

All simulated conversations go through the same `/api/chat` endpoint as real users, which means they **are stored in your Supabase database** in the `messages` table.

## How They're Differentiated

### Session ID Prefix: `sim_`

All simulated conversations use session IDs with the pattern:
```
sim_{persona_id}_{scenario_id}_{seed}
```

**Examples:**
```
sim_persona_001_frustrated_commuter_scenario_005_network_issue_43
sim_persona_002_tech_savvy_student_scenario_001_esim_setup_44
sim_persona_003_elderly_confused_scenario_002_roaming_activation_45
```

### Database Schema

From `app/models.py`, messages are stored with:
```python
{
  "session_id": str,              # Contains "sim_" prefix for test data
  "role": str,                    # "user" or "assistant"
  "content": str,                 # Message text
  "participant_id": Optional[str],
  "participant_name": Optional[str],
  "participant_group": str        # "A" or "B"
}
```

## Filtering Test Data

### SQL Queries

To exclude simulated conversations from analytics:

```sql
-- Get only real user messages
SELECT * FROM messages
WHERE session_id NOT LIKE 'sim_%';

-- Count real vs simulated conversations
SELECT
  CASE
    WHEN session_id LIKE 'sim_%' THEN 'simulated'
    ELSE 'real'
  END as user_type,
  COUNT(DISTINCT session_id) as conversation_count
FROM messages
GROUP BY user_type;

-- Real user statistics only
SELECT
  participant_group,
  COUNT(DISTINCT session_id) as conversations,
  AVG(LENGTH(content)) as avg_message_length
FROM messages
WHERE session_id NOT LIKE 'sim_%'
  AND role = 'user'
GROUP BY participant_group;
```

### Supabase Dashboard Filters

In Supabase Table Editor or API queries:
```
session_id.not.like.sim_%
```

## Recommendations

### 1. Add Participant ID for Simulated Users

Consider setting `participant_id` to identify the simulation run:

**Update in `/Users/stagcto/fyp/llm-testing/src/api/client.py`:**

```python
def send_message(
    self,
    message: str,
    session_id: str,
    participant_group: str = "A",
    participant_id: str = None  # Add this
) -> Dict[str, Any]:
    payload = {
        "message": message,
        "session_id": session_id,
        "participant_group": participant_group,
        "participant_id": participant_id  # Pass through
    }
```

**Then in orchestrator, pass a simulation identifier:**

```python
participant_id = f"llm_test_{experiment_id}"
```

This would make filtering even clearer.

### 2. Create a Database View for Real Users

Create a Supabase view that automatically filters:

```sql
CREATE VIEW messages_real_users AS
SELECT * FROM messages
WHERE session_id NOT LIKE 'sim_%';

CREATE VIEW participants_real_users AS
SELECT * FROM participants
WHERE session_id NOT LIKE 'sim_%';
```

Then query `messages_real_users` instead of `messages` in your analytics.

### 3. Add Metadata Column (Future Enhancement)

If you want more explicit tracking, add a `metadata` JSON column:

```sql
ALTER TABLE messages
ADD COLUMN metadata JSONB;
```

Then store:
```json
{
  "source": "llm_test",
  "experiment_id": "exp_20260128_143022",
  "persona_id": "persona_001_frustrated_commuter",
  "scenario_id": "scenario_005_network_issue"
}
```

### 4. Cleanup Strategy

You may want to periodically clean up test data:

```sql
-- Delete all simulated conversations older than 30 days
DELETE FROM messages
WHERE session_id LIKE 'sim_%'
  AND created_at < NOW() - INTERVAL '30 days';

-- Or keep only the most recent N simulated conversations
DELETE FROM messages
WHERE session_id IN (
  SELECT DISTINCT session_id
  FROM messages
  WHERE session_id LIKE 'sim_%'
  ORDER BY created_at DESC
  OFFSET 1000  -- Keep most recent 1000 test sessions
);
```

## Current State Check

To see how many simulated conversations you currently have:

```sql
SELECT
  COUNT(DISTINCT session_id) as total_sessions,
  COUNT(DISTINCT CASE WHEN session_id LIKE 'sim_%' THEN session_id END) as simulated_sessions,
  COUNT(DISTINCT CASE WHEN session_id NOT LIKE 'sim_%' THEN session_id END) as real_sessions
FROM messages;
```

## Impact on Analytics

### Be Careful With:

1. **Aggregate Statistics** - Exclude test data from production metrics
2. **A/B Test Results** - Only analyze real users for valid statistical significance
3. **User Behavior Analysis** - Simulated personas have predefined behaviors
4. **Performance Metrics** - Test data may have different latency patterns
5. **Cost Analysis** - Track OpenAI costs separately for testing vs production

### Safe to Include:

1. **System Performance Testing** - Database query performance
2. **API Load Testing** - Understanding throughput capabilities
3. **Chatbot Quality Evaluation** - That's the whole point!

## Example: Modified Analytics Query

**Before (includes test data):**
```sql
SELECT participant_group, AVG(rating_overall)
FROM feedback
GROUP BY participant_group;
```

**After (real users only):**
```sql
SELECT participant_group, AVG(rating_overall)
FROM feedback
WHERE session_id NOT LIKE 'sim_%'
GROUP BY participant_group;
```

## Verification Script

Run this to check current database state:

```python
from app.storage import SupabaseStore

store = SupabaseStore()

# Get message counts
rows, code = store.select_rows(
    "messages",
    params={},
    select="session_id"
)

sessions = set(r['session_id'] for r in rows)
sim_sessions = [s for s in sessions if s.startswith('sim_')]
real_sessions = [s for s in sessions if not s.startswith('sim_')]

print(f"Total sessions: {len(sessions)}")
print(f"Simulated: {len(sim_sessions)}")
print(f"Real users: {len(real_sessions)}")
print(f"\nExample simulated session IDs:")
for s in sim_sessions[:5]:
    print(f"  - {s}")
```

## Summary

✅ **Good News:**
- Test data is clearly marked with `sim_` prefix
- Easy to filter in SQL queries
- No risk of accidentally analyzing test data if you use proper WHERE clauses

⚠️ **Action Items:**
1. Update all analytics queries to exclude `session_id LIKE 'sim_%'`
2. Create database views for real users only
3. Consider adding cleanup scripts for old test data
4. Document this filtering requirement for future team members

The current approach is solid - the `sim_` prefix provides clear separation. Just make sure anyone analyzing the data knows to filter it out!
