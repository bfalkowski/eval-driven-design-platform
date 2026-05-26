# Eval Driven Design Platform

A clean-room **control plane for eval-driven AI development** on top of [Langfuse](https://langfuse.com).

The platform shows how teams can define success criteria, turn observed failures into reusable eval cases, run candidate prompts/models/workflows, push scores back to Langfuse, and enforce quality gates before shipping AI changes.

**This project does not replace Langfuse.** Langfuse remains the observability and evaluation data plane. EDD provides the engineering workflow around it.

## What you get (target MVP)

- **EvalSpec** — what “good” means (rubric, thresholds, judge config)
- **EvalCase** — reusable cases (manual or imported from Langfuse traces)
- **ExperimentRun** — compare candidates (`prompt_v3` vs `prompt_v4`)
- **Quality gates** — CI-style pass/fail on thresholds
- **Streamlit console** — Observe → Case → Run → Evaluate → Decide
- **Langfuse adapter** — optional link, score push, trace import (later phases)

## Repo layout

```text
api/       FastAPI control plane (edd-api)
console/   Streamlit operator UI (edd-console)
worker/    Experiment runner (edd-worker)
deploy/    docker-compose, Helm (later)
scripts/   local_e2e.sh, build_images.sh
docs/      architecture and integration notes
```

## Quick start

```bash
cd eval-driven-design-platform
cp .env.example .env

# Recommended: Postgres in Docker, API + console on host
./scripts/local_e2e.sh --postgres

# With Langfuse overlay (UI on http://localhost:3001)
./scripts/local_e2e.sh --postgres --langfuse
```

- Console: http://localhost:8501 — paste the **Bearer token** printed by the script  
- API: http://localhost:8000/docs  
- Langfuse (with `--langfuse`): http://localhost:3001 — `admin@local.dev` / `local-demo-password`  

Without `--langfuse`, the console correctly shows Langfuse as **Disabled** — integration is optional.

Full Docker compose (heavier; needs stable Colima):

```bash
./scripts/compose_up_langfuse.sh
```

Stop:

```bash
./scripts/local_e2e.sh --stop
```

## Tests

```bash
make test
# or
cd api && uv run pytest -q
```

## Plan

Implementation is phased in **`EVAL_DRIVEN_DESIGN_PLAN.md`**. Build incrementally; do not skip validation gates.

## Status

**Phase 0** — monorepo skeleton, health endpoints, console overview, compose stack.  
**Phase 0.5** — platform spine imported from starter repos (auth, metrics, OTel, Postgres path, Operations console, Helm skeleton).  
**Phase 1** — EvalSpec/EvalCase CRUD, tenant-scoped repositories, Alembic migration.  
**Phase 2** — Experiment runs, deterministic mock evaluation, run summaries, seed script.  
**Phase 3** — Streamlit console MVP for specs, cases, runs, and results.  
**Phase 4** — Optional Langfuse adapter, health endpoint, local compose overlay.  
**Phase 5+** — score push, trace import, quality gates (see plan).
