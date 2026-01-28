# LLM Testing Framework for VodaCare Chatbot

A Python CLI framework for testing chatbot interactions using LLM-as-user simulation and LLM-as-judge evaluation methodology.

## Overview

This framework simulates diverse user personas interacting with the VodaCare chatbot across various support scenarios, then evaluates the quality of those interactions using both LLM-based scoring and deterministic heuristic checks.

**Key Features:**
- 5 distinct user personas with different personalities, tech literacy levels, and communication styles
- 5 common support scenarios (eSIM setup, roaming, billing, plan upgrades, network issues)
- LLM-powered user simulation for realistic multi-turn conversations
- GPT-4-based evaluation judge with rubric scoring
- Deterministic heuristic safety checks
- Reproducible experiments with seeded random generation
- JSON artifact outputs for analysis

## Installation

1. Create a virtual environment:
```bash
cd /Users/stagcto/fyp/llm-testing
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Configuration

Edit `.env` file:

```bash
# API Configuration
VODACARE_API_BASE_URL=http://localhost:8000
API_TIMEOUT=30

# OpenAI Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL_SIMULATOR=gpt-4o-mini    # Model for user simulation
OPENAI_MODEL_JUDGE=gpt-4o              # Model for evaluation

# Experiment Settings
EXPERIMENT_SEED=42
MAX_TURNS=10
OUTPUT_DIR=./outputs
LOG_LEVEL=INFO
```

## Available Personas

1. **persona_001_frustrated_commuter** - Alex Chen, 34, London
   - Frustrated software developer with network issues on commute
   - Low patience, direct communication, moderate tech literacy

2. **persona_002_tech_savvy_student** - Jamie Smith, 21, Manchester
   - Tech-savvy university student seeking best streaming plan
   - High patience, casual tone, high tech literacy

3. **persona_003_elderly_confused** - Margaret Brown, 72, Brighton
   - Retired teacher needing patient guidance with new smartphone
   - Moderate patience, polite/confused tone, low tech literacy

4. **persona_004_busy_parent** - Priya Patel, 38, Birmingham
   - Time-pressured marketing manager with billing question
   - Low patience, professional tone, moderate tech literacy

5. **persona_005_international_traveler** - Carlos Garcia, 45, London
   - Business consultant anxious about roaming charges
   - Moderate patience, detail-oriented, moderate tech literacy

## Available Scenarios

1. **scenario_001_esim_setup** - eSIM setup and activation
2. **scenario_002_roaming_activation** - International roaming configuration
3. **scenario_003_billing_dispute** - Billing inquiry and dispute resolution
4. **scenario_004_plan_upgrade** - Mobile plan comparison and upgrade
5. **scenario_005_network_issue** - Network connectivity troubleshooting

## Usage

### Prerequisites

Make sure the VodaCare server is running:
```bash
cd /Users/stagcto/fyp/server
uvicorn app.main:app --reload
```

### List Available Options

```bash
# List all personas
python run_experiment.py --list-personas

# List all scenarios
python run_experiment.py --list-scenarios
```

### Run Single Test

Test one persona with one scenario:
```bash
python run_experiment.py \
  --variant A \
  --personas persona_001_frustrated_commuter \
  --scenarios scenario_005_network_issue \
  --name "single_test"
```

### Run Multiple Combinations

Test specific personas and scenarios:
```bash
python run_experiment.py \
  --variant A \
  --personas persona_001,persona_002,persona_003 \
  --scenarios scenario_001,scenario_005 \
  --name "subset_test"
```

### Run Full Experiment

Test all personas with all scenarios (25 conversations):
```bash
python run_experiment.py \
  --variant A \
  --personas all \
  --scenarios all \
  --name "full_baseline"
```

### Compare Variants

```bash
# Run variant A (Kindness system prompt)
python run_experiment.py \
  --variant A \
  --personas all \
  --scenarios all \
  --name "variant_a_baseline"

# Run variant B (Confirmation system prompt)
python run_experiment.py \
  --variant B \
  --personas all \
  --scenarios all \
  --name "variant_b_baseline"
```

### Dry Run

Preview what would be tested without running:
```bash
python run_experiment.py \
  --variant A \
  --personas all \
  --scenarios all \
  --dry-run
```

## Output Artifacts

All outputs are saved to `./outputs/` directory:

### Full Experiment Results
`exp_A_variant_a_baseline_20260128_143022.json`
- Complete conversation transcripts
- Turn-by-turn messages and timestamps
- LLM evaluation scores with rationale
- Heuristic check results
- Metadata and configuration snapshot

### Summary Statistics
`summary_A_variant_a_baseline_20260128_143022.json`
- Aggregated scores across all conversations
- Success rates and termination breakdowns
- Average performance metrics
- Scores by persona and scenario

## Evaluation Methodology

### LLM Judge (GPT-4)

Scores conversations on 4 dimensions (0.0-1.0 scale):

1. **Task Success (50% weight)** - Did the conversation achieve the scenario's success criteria?
2. **Clarity (20% weight)** - Were responses clear and appropriate for the user's tech literacy?
3. **Empathy (20% weight)** - Was the tone appropriate for the user's emotional state?
4. **Policy Compliance (10% weight)** - Were there any policy violations or hallucinated information?

### Heuristic Checks

Deterministic safety checks:

1. **No Hallucinated Plans** - Validates all mentioned prices against valid plan catalog (£8-£85)
2. **No Contradictions** - Checks for inconsistent information across conversation turns
3. **Appropriate Response Length** - Ensures responses are 30-400 words
4. **Escalation Appropriateness** - Verifies escalation was offered when needed

## Reproducibility

Experiments are reproducible through:
- Fixed base seed (configurable in `.env`)
- Per-turn seed calculation (base_seed + turn_number)
- Deterministic LLM generation with seed parameter
- Locked dependency versions

## Architecture

```
llm-testing/
├── run_experiment.py           # CLI entry point
├── config/
│   ├── settings.py             # Configuration loader
│   └── evaluation_rubric.yaml  # Scoring criteria
├── data/
│   ├── personas/               # 5 persona YAML files
│   └── scenarios/              # 5 scenario YAML files
├── src/
│   ├── persona/                # Persona models and loader
│   ├── scenario/               # Scenario models and loader
│   ├── simulator/              # LLM-as-user simulator
│   ├── orchestrator/           # Conversation orchestration
│   ├── evaluator/              # LLM judge and heuristics
│   ├── api/                    # VodaCare API client
│   ├── experiment/             # Experiment runner
│   └── artifacts/              # Result models and writer
└── outputs/                    # Generated artifacts (gitignored)
```

## Example Workflow

```bash
# 1. Start VodaCare server
cd /Users/stagcto/fyp/server
uvicorn app.main:app --reload &

# 2. Run quick test
cd /Users/stagcto/fyp/llm-testing
python run_experiment.py \
  --variant A \
  --personas persona_001_frustrated_commuter \
  --scenarios scenario_005_network_issue \
  --name "quick_test"

# 3. Check results
cat outputs/summary_A_quick_test_*.json | jq '.summary'

# 4. Run full experiment
python run_experiment.py \
  --variant A \
  --personas all \
  --scenarios all \
  --name "full_baseline"

# 5. Compare with variant B
python run_experiment.py \
  --variant B \
  --personas all \
  --scenarios all \
  --name "full_baseline"
```

## Troubleshooting

### API Connection Error
```
Failed to connect to API at http://localhost:8000/api/chat
```
**Solution:** Ensure VodaCare server is running: `uvicorn app.main:app --reload`

### OpenAI API Key Missing
```
ValueError: OPENAI_API_KEY must be set in .env file
```
**Solution:** Add your OpenAI API key to `.env` file

### Rate Limits
If you hit OpenAI rate limits, the experiment will log errors but continue. Check `experiment.log` for details.

## Logs

- **Console output:** Real-time progress and summary
- **experiment.log:** Detailed logs including API calls, errors, and debug info

## Extending the Framework

### Add New Persona

1. Create YAML file in `data/personas/`:
```yaml
id: persona_006_new_persona
name: Your Name
age: 30
# ... see existing personas for full structure
```

2. Run with new persona:
```bash
python run_experiment.py --variant A --personas persona_006_new_persona --scenarios all
```

### Add New Scenario

1. Create YAML file in `data/scenarios/`:
```yaml
id: scenario_006_new_scenario
name: New Scenario
topic: billing
# ... see existing scenarios for full structure
```

2. Run with new scenario:
```bash
python run_experiment.py --variant A --personas all --scenarios scenario_006_new_scenario
```

## License

Internal use only - FYP project.

## Support

For issues or questions, check `experiment.log` or review the conversation transcripts in output artifacts.
