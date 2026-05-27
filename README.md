# Eval Driven Design Platform

A clean-room **control plane for eval-driven AI development** on top of [Langfuse](https://langfuse.com).

The platform shows how teams can define success criteria, turn observed failures into
reusable eval cases, run candidate prompts/models/workflows, push scores back to
Langfuse, and enforce quality gates before shipping AI changes.

**This project does not replace Langfuse.** Langfuse remains the observability and evaluation data plane. EDD provides the engineering workflow around it.

You can run the stack locally to walk through the operator loop end to end, with optional Langfuse integration.

## Console

Streamlit operator UI — Observe → Case → Run → Evaluate → Decide:

![Eval Driven Design Platform console — Overview](docs/images/console-overview.jpg)

## Why this exists

AI teams often discover failures through traces, logs, support escalations, or manual testing, but those failures do not automatically become reusable engineering assets.

This project explores an **eval-driven design** workflow where:

- observed failures become **eval cases**
- eval cases become **repeatable experiments**
- experiment results become **quality gates** before AI changes ship

## What this demonstrates

- Evaluation-driven design for AI workflows
- Turning observed failures into reusable eval cases (including Langfuse trace import)
- Separating eval specs, cases, experiment runs, and quality gates (gate execution planned)
- Using observability and traces as part of the development loop
- Treating AI behavior as measurable and testable before release (deterministic mock evaluator today)
- Designing a lightweight platform / control-plane abstraction around Langfuse
- Monorepo hygiene: FastAPI, Streamlit, Postgres, Docker/Kubernetes scaffolding, and CI checks

## Architecture

```mermaid
flowchart TD
  Operator[Operator / Engineer] --> Console[Streamlit Console]
  Console --> API[FastAPI Control Plane]
  API --> DB[(Postgres)]
  API --> Worker[Worker / Evaluator]
  Worker --> Langfuse[Langfuse Adapter]
  Langfuse --> Observability[Traces / Scores / Analytics]
```

**Today:** experiment scaffold and mock evaluation run **in the API**; the worker image
provides logging, OTel, and deploy parity. Async worker-backed runs are planned. The
Langfuse adapter is invoked from the API when integration is enabled.

## Demo flow

1. **Define an EvalSpec** — what success means (rubric, pass threshold).
2. **Add EvalCases** — manually or by importing a Langfuse trace.
3. **Run an ExperimentRun** — against a candidate version (e.g. `prompt_v4`).
4. **Review results** — scores, justifications, and Langfuse trace links in the console.
5. **Iterate** — adjust the candidate or cases and re-run.
6. **Quality gate** *(planned)* — CI-style pass/fail on thresholds before shipping a change.

With Langfuse enabled (`./scripts/local_e2e.sh --postgres --langfuse`), runs can create traces and push scores when integration is configured.

## What you get (target MVP)

- **EvalSpec** — what “good” means (rubric, thresholds, judge config)
- **EvalCase** — reusable cases (manual or imported from Langfuse traces)
- **ExperimentRun** — compare candidates (`prompt_v3` vs `prompt_v4`)
- **Quality gates** — CI-style pass/fail on thresholds *(planned — Phase 7)*
- **Streamlit console** — Observe → Case → Run → Evaluate → Decide
- **Langfuse adapter** — health, trace fetch, import case, score push, trace create on run

## Current status

### Implemented

- Monorepo: `api/`, `console/`, `worker/`, `deploy/`, `scripts/`
- FastAPI control plane: health, ready, metrics, demo JWT auth, tenant-scoped APIs
- **EvalSpec** and **EvalCase** CRUD (Postgres and in-memory storage)
- **ExperimentRun** API with deterministic mock scaffold and mock evaluator
- Run summaries and **evaluation results** listing
- Streamlit console: Overview, Eval Specs, Cases, Runs, Results Explorer, Langfuse, Operations
- Optional **Langfuse**: health, get trace, import case, push scores, create trace on run
- Local dev: `local_e2e.sh`, seed script, Docker images, Helm skeleton
- CI: tests, Ruff, mypy, OpenAPI drift, pip-audit, Dockerfile policy, image builds, kubeconform

### Remaining

See **`EVAL_DRIVEN_DESIGN_PLAN.md`** for Phases 7–8 (quality gates, demo polish).

| Phase | Scope | Status |
|-------|--------|--------|
| 0–4 | Skeleton, platform spine, CRUD, Langfuse adapter | Done |
| 5–6 | Score push, trace links, trace import | Done |
| 7 | Quality gates | Planned |
| 8 | Demo script and baseline polish | Planned |

## Repo layout

```text
api/       FastAPI control plane (edd-api)
console/   Streamlit operator UI (edd-console)
worker/    Platform shell (OTel/logging; async eval jobs later)
deploy/    docker-compose, Helm
scripts/   local_e2e.sh, build_images.sh, seed_demo_data.py
```

## Quick start

```bash
cd eval-driven-design-platform
cp .env.example .env
./scripts/local_e2e.sh --postgres
./scripts/local_e2e.sh --postgres --langfuse   # optional Langfuse UI
```

- Console: http://localhost:8501 (Bearer token printed by the script)
- API: http://localhost:8000/docs
- Langfuse: http://localhost:3001 when using `--langfuse` (`admin@local.dev` / `local-demo-password`)

Stop: `./scripts/local_e2e.sh --stop`

## Tests

```bash
make test
```

## CI

GitHub Actions: API/console tests, Ruff, mypy, OpenAPI drift, pip-audit, Dockerfile policy, package and image builds, Helm/kubeconform.

## Plan

Phased implementation is documented in **`EVAL_DRIVEN_DESIGN_PLAN.md`**.
