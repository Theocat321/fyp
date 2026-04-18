# VodaCare Support

A telecom customer support chatbot built as a research platform for a Final Year Project. The system supports two prompt variants (A/B), logs interaction telemetry, collects rubric-aligned user feedback, and includes a full LLM-simulated testing framework to mirror the human study.

## Research Question

**Can LLM-simulated users substitute for human participants in chatbot evaluation?**

The study compared two assistant modes — Variant A (open, empathetic tone) and Variant B (strict, topic-restricted) — across both an LLM simulation (200 conversations, 5 personas × 5 scenarios × 2 variants × 4 runs) and a live human study (88 sessions). Both were evaluated using the same LLM-as-Judge rubric (Task Success, Clarity, Empathy) to test whether simulation reproduces human findings.

## Key Findings

| Metric | Sim A | Sim B | Human A | Human B |
|---|---|---|---|---|
| Overall (0–1) | 0.563 | 0.514 | 0.89 | 0.82 |
| Task Success | 0.347 | 0.351 | 0.83 | 0.83 |
| Clarity | 0.709 | 0.721 | 0.91 | 0.89 |
| Empathy | **0.844** | **0.545** | **0.96** | **0.60** |

- Variant A outperforms Variant B in every evaluation method (simulation LAJ, human LAJ, human self-rating).
- Empathy is the sharpest differentiator — the gap is consistent across simulation and human results, suggesting simulation reliably surfaces prompt-level empathy differences.
- Task success is scenario-driven, not variant-driven — both groups score identically (0.83 LAJ, 4.06/5 self-rated).
- Simulation scores are lower overall (~0.51–0.56 vs ~0.82–0.89) because synthetic personas apply stricter success criteria and include adversarial types (rude, impatient, troll).

Full results: [`docs/results/RESULTS_SUMMARY.md`](docs/results/RESULTS_SUMMARY.md)

## Project Structure

```
server/          FastAPI backend — intent detection, LLM integration, telemetry
web/             Next.js frontend — chat UI, enrollment, feedback, scenario selection
llm-testing/     LLM simulation framework — personas, scenarios, evaluation pipeline
docs/            Design document, testing guide, data pipelines, study results
```

## Quick Start

Prerequisites: Node.js 18+, Python 3.10+. Frontend runs on port 3000, backend on 8000.

**1. Environment**

Copy `.env.example` to `.env` in the repo root. Both apps load it automatically in dev.

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

To enable LLM-generated replies, set in root `.env`:

```
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
```

Without these, the chatbot falls back to rule-based responses.

### Assistant mode

Controls the prompt variant used:

```
ASSISTANT_MODE=open    # Variant A — general chat allowed, empathetic tone (default)
ASSISTANT_MODE=strict  # Variant B — restricted to telecom topics
```

### Streaming (SSE)

```
NEXT_PUBLIC_USE_STREAMING=true
```

Switches the frontend to the `/api/chat-stream` endpoint, which streams tokens via Server-Sent Events.

### Supabase (optional)

For message persistence and telemetry logging, set in `.env`:

```
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
```

Required tables: `participants`, `messages`, `interactions`, `interaction_events`. Schemas in [`docs/DESIGN.md`](docs/DESIGN.md) and `res/verbose_interactions.sql`. The app degrades gracefully without Supabase — telemetry events return 202 and are not stored.

### Deployment

Single Vercel project from the repo root via `vercel.json`. Next.js builds from `web/`; Python runs as Vercel Serverless Functions from `server/api/`. Set env vars in the Vercel dashboard. Do not set `NEXT_PUBLIC_API_BASE_URL` on Vercel — leave it empty so the UI calls the built-in routes.

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

See [`llm-testing/README.md`](llm-testing/README.md) for full framework documentation.

## Further Reading

- [`docs/DESIGN.md`](docs/DESIGN.md) — full system design and architecture
- [`docs/results/`](docs/results/) — study results, behaviour analysis, human feedback
- [`docs/TESTING_GUIDE.md`](docs/TESTING_GUIDE.md) — evaluation methodology
- [`docs/DATA_PIPELINES.md`](docs/DATA_PIPELINES.md) — data pipeline architecture
- [`llm-testing/README.md`](llm-testing/README.md) — simulation framework
