# Testing Guide for LLM Testing Framework

## Implementation Status: COMPLETE ✓

All components have been successfully implemented:

- ✓ Directory structure and configuration
- ✓ 5 user personas with detailed profiles
- ✓ 5 test scenarios covering key support topics
- ✓ Pydantic data models
- ✓ YAML loaders for personas and scenarios
- ✓ API client for VodaCare
- ✓ LLM-as-user simulator
- ✓ Conversation orchestrator with termination logic
- ✓ LLM judge evaluator
- ✓ Heuristic safety checks
- ✓ Experiment runner
- ✓ Artifact writer
- ✓ CLI entry point
- ✓ Documentation and examples

## Prerequisites for Testing

### 1. OpenAI API Key

You need an OpenAI API key to run experiments. Update `.env`:

```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

### 2. VodaCare Server Running

Start the VodaCare server in a separate terminal:

```bash
cd /Users/stagcto/fyp/server
uvicorn app.main:app --reload
```

Verify it's running:
```bash
curl http://localhost:8000/health
```

### 3. Activate Virtual Environment

```bash
cd /Users/stagcto/fyp/llm-testing
source venv/bin/activate
```

## Quick Validation Tests

### Test 1: List Available Options

```bash
# List personas
python3 run_experiment.py --list-personas

# List scenarios
python3 run_experiment.py --list-scenarios
```

**Expected output:** Should show 5 personas and 5 scenarios

### Test 2: Dry Run

```bash
python3 run_experiment.py \
  --variant A \
  --personas persona_001_frustrated_commuter \
  --scenarios scenario_005_network_issue \
  --dry-run
```

**Expected output:** Should show what would be tested without running

### Test 3: Single Conversation Test

This will actually run one conversation (requires OpenAI API key and VodaCare server):

```bash
python3 run_experiment.py \
  --variant A \
  --personas persona_001_frustrated_commuter \
  --scenarios scenario_005_network_issue \
  --name "integration_test"
```

**Expected behavior:**
1. Connects to VodaCare API at localhost:8000
2. Simulates frustrated commuter with network issue
3. Runs multi-turn conversation (up to 10 turns or until termination)
4. Evaluates with LLM judge (GPT-4)
5. Runs heuristic checks
6. Writes results to `outputs/`

**Expected output files:**
- `outputs/exp_A_integration_test_*.json` - Full experiment results
- `outputs/summary_A_integration_test_*.json` - Summary statistics
- `experiment.log` - Detailed logs

**Console output should show:**
- Turn-by-turn conversation progress
- Evaluation scores
- Summary statistics

### Test 4: Multiple Conversations

Test 2 personas × 2 scenarios = 4 conversations:

```bash
python3 run_experiment.py \
  --variant A \
  --personas persona_001,persona_002 \
  --scenarios scenario_001,scenario_005 \
  --name "subset_test"
```

### Test 5: Full Experiment

Test all 5 personas × 5 scenarios = 25 conversations:

```bash
python3 run_experiment.py \
  --variant A \
  --personas all \
  --scenarios all \
  --name "full_baseline"
```

**Note:** This will take approximately 10-15 minutes and will make ~75 OpenAI API calls (25 for simulation, 25 for evaluation, plus some extras).

## Verification Checklist

After running Test 3 (single conversation), verify:

- [ ] Output files exist in `outputs/` directory
- [ ] Full experiment JSON has complete transcript with turns
- [ ] Each turn has user and assistant messages
- [ ] Termination info shows reason (satisfaction, max_turns, etc.)
- [ ] LLM evaluation has scores for all 4 dimensions (0.0-1.0)
- [ ] LLM evaluation includes rationale text
- [ ] Heuristic results show all 4 checks
- [ ] No critical failures in heuristics (unless there's a real issue)
- [ ] Summary statistics are calculated
- [ ] Console shows formatted summary

### Example Valid Output Structure

```json
{
  "run_id": "run_exp_...",
  "persona_id": "persona_001_frustrated_commuter",
  "scenario_id": "scenario_005_network_issue",
  "variant": "A",
  "transcript": [
    {
      "turn_number": 1,
      "speaker": "user",
      "message": "Signal keeps dropping on my train...",
      "timestamp": "..."
    },
    {
      "turn_number": 1,
      "speaker": "assistant",
      "message": "I understand how frustrating...",
      "timestamp": "...",
      "metadata": {"latency_ms": 1234.5}
    }
  ],
  "llm_evaluation": {
    "task_success": 0.85,
    "clarity": 0.90,
    "empathy": 0.75,
    "policy_compliance": 1.0,
    "overall_weighted": 0.855,
    "rationale": "..."
  },
  "heuristic_results": {
    "checks": [...],
    "all_passed": true,
    "critical_failures": []
  }
}
```

## Troubleshooting

### Error: "OPENAI_API_KEY must be set"
- Edit `.env` file and add your OpenAI API key

### Error: "Failed to connect to API"
- Start the VodaCare server: `cd /Users/stagcto/fyp/server && uvicorn app.main:app --reload`
- Check it's running: `curl http://localhost:8000/health`

### Error: "No module named 'src'"
- Make sure you're in the llm-testing directory: `cd /Users/stagcto/fyp/llm-testing`
- Activate virtual environment: `source venv/bin/activate`

### OpenAI Rate Limits
- If you hit rate limits, wait a few minutes between experiments
- Consider using smaller subset tests first
- Check `experiment.log` for detailed error messages

### Empty or Invalid Responses
- Check VodaCare server logs for errors
- Verify the variant ("A" or "B") matches system prompts in server
- Look at full transcript in output JSON to debug

## Expected Behavior

### Conversation Flow
1. User simulator starts with seed utterance from persona
2. VodaCare responds via API
3. User simulator generates contextual follow-up based on persona + history
4. Continues until termination condition met:
   - User satisfaction detected
   - Max turns reached (10)
   - User requests escalation
   - Stalemate/frustration detected
   - Persona patience exceeded

### Evaluation Flow
1. LLM judge reviews full transcript
2. Scores 4 dimensions based on rubric
3. Provides rationale for each score
4. Heuristic checks validate safety constraints
5. Results combined into ConversationRun artifact

### Success Criteria
- Conversations don't all hit max_turns (shows natural termination)
- LLM scores are in valid range (0.0-1.0)
- Heuristic checks pass for most conversations
- Different personas show different conversation patterns
- Variant A and B show measurable differences in empathy scores

## Next Steps

1. Run Test 3 (single conversation) to validate end-to-end flow
2. Inspect output JSON to verify structure
3. Run Test 4 (subset) to verify multiple conversations work
4. Run Test 5 (full experiment) for both variants A and B
5. Compare summary statistics between variants
6. Analyze individual conversation transcripts for insights

## Framework Capabilities

This framework can now:
- Simulate 5 distinct user personas with realistic behavior
- Test 5 common support scenarios
- Generate natural multi-turn conversations
- Evaluate conversation quality across 4 dimensions
- Detect safety issues (hallucinated info, contradictions)
- Produce detailed JSON artifacts for analysis
- Run reproducible experiments with seeded randomness
- Scale from single tests to full 25-conversation experiments

## Files to Examine

- `outputs/exp_*.json` - Full experiment with all conversations
- `outputs/summary_*.json` - Aggregated statistics
- `experiment.log` - Detailed execution logs
- `examples/sample_output.json` - Expected output format
