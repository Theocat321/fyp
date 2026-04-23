# VodaCare Support

Telecom customer support chatbot built as a research platform. Two prompt variants (A/B), interaction telemetry, rubric-aligned feedback, and an LLM simulation framework mirroring the human study.

## Research Questions

- **RQ1:** Do prompt tone variants (empathetic vs. concise) produce measurable behavioural differences?
- **RQ2:** Do LLM persona simulations reproduce human behavioural trends under identical conditions?
- **RQ3:** Does LLM-as-a-Judge align with human feedback, and does it add signal beyond numeric ratings?

Variant A (Kindness: empathetic) vs Variant B (Confirmation: concise, task-focused) — 200 simulated conversations (20 personas × 5 runs × 2 variants) + 85 human sessions across 18 participants. Evaluated with LLM-as-Judge, human self-ratings, and behavioural telemetry.

## Key Findings

| Metric | Sim A | Sim B | Human A | Human B |
|---|---|---|---|---|
| Overall (0–1) | 0.582 | 0.514 | 0.89 | 0.82 |
| Task Success | 0.365 | 0.351 | 0.83 | 0.83 |
| Clarity | 0.717 | 0.721 | 0.91 | 0.89 |
| Empathy | **0.865** | **0.545** | **0.96** | **0.60** |

- Empathy only dimension where all three methods converge on a large gap — sim LAJ (+0.320), human LAJ (+0.36), self-ratings (4.50 vs 3.90).
- Task success scenario-driven, not variant-driven — identical across groups (LAJ: 0.83, self-rated: 4.06/5).
- Group A shorter sessions (323s vs 428s), fewer turns (3.9 vs 4.4), longer messages (19s vs 12s typing) — same task success.
- Simulation correctly predicted direction of every human finding.
- Simulation scores lower overall — adversarial personas (rude, impatient, troll) and stricter success criteria.

## Project Structure

```
server/          FastAPI backend — intent detection, LLM integration, telemetry
web/             Next.js frontend — chat UI, enrollment, feedback, scenario selection
llm-testing/     LLM simulation framework — personas, scenarios, evaluation pipeline
docs/            Design document, testing guide, data pipelines, study results
```

## Quick Start

Node.js 18+, Python 3.10+. Frontend on port 3000, backend on 8000.

**1. Environment**

Copy `.env.example` to `.env` in the repo root.

**2. Backend**

```bash
cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**3. Frontend**

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:3000`.

## Configuration

### OpenAI (optional)

```
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
```

Falls back to rule-based responses without these.

### Assistant mode

```
ASSISTANT_MODE=open    # Variant A — empathetic tone (default)
ASSISTANT_MODE=strict  # Variant B — concise, task-focused
```

### Streaming (SSE)

```
NEXT_PUBLIC_USE_STREAMING=true
```

Switches to `/api/chat-stream` for token streaming via Server-Sent Events.

### Supabase (optional)

```
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
```

Required tables: `participants`, `messages`, `interactions`, `interaction_events`. Schemas in [`docs/DESIGN.md`](docs/DESIGN.md) and `res/verbose_interactions.sql`. Degrades gracefully without Supabase — telemetry returns 202, nothing stored.

### Deployment

Single Vercel project via `vercel.json`. Next.js from `web/`, Python as Serverless Functions from `server/api/`. Leave `NEXT_PUBLIC_API_BASE_URL` unset on Vercel.

## Running the LLM Tests

```bash
cd llm-testing
python run_experiment.py --variant A --personas all --scenarios all
```

```bash
python evaluate_human_transcripts.py --all --output human_evals.json
```

```bash
python generate_comparison_report.py \
  --llm-results "outputs/exp_*.json" \
  --human-results "human_evals.json" \
  --output "report.html"
```

See [`llm-testing/README.md`](llm-testing/README.md) for full framework docs.

## Further Reading

- [`docs/DESIGN.md`](docs/DESIGN.md) — system design and architecture
- [`docs/results/`](docs/results/) — study results, behaviour analysis, human feedback
- [`docs/TESTING_GUIDE.md`](docs/TESTING_GUIDE.md) — evaluation methodology
- [`docs/DATA_PIPELINES.md`](docs/DATA_PIPELINES.md) — data pipeline architecture
- [`llm-testing/README.md`](llm-testing/README.md) — simulation framework
