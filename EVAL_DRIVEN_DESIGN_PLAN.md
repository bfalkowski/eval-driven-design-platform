# Eval Driven Design Platform — Build Plan

Canonical north star for this monorepo (committed). Build **phase by phase**; do not skip validation.

For your original long-form spec (UI pages, SQL, payloads, Cursor prompts), keep a private copy at `.local/PRODUCT_SPEC_REFERENCE.md` — not in git, so contributors and agents are not pulled between two public docs.

## 1. Product summary

**Eval Driven Design (EDD)** combines:

- Deterministic application scaffolding
- Langfuse-backed traces and scores
- Reusable eval cases and versioned eval specs
- Experiment runs across candidate prompts/models/workflows
- CI-style quality gates

**One line:** A lightweight eval-driven design control plane on Langfuse — observe traces, convert failures into eval cases, run candidates, score results, enforce gates before shipping AI changes.

## 2. Design principle

The **evaluated workflow** is the product boundary — not the LLM call.

Answer: *Given this task, eval spec, case set, scaffold, candidate version, and judge config — is this workflow good enough to ship?*

## 3. Architecture

```text
Operator → Streamlit Console → FastAPI Control Plane → Postgres
                                      ↓
                              Worker / Evaluator
                              (scaffold + mock judge)
                                      ↓
                              Langfuse Adapter (optional)
```

Langfuse: trace inspection, observations, score analytics.  
EDD: EvalSpec, EvalCase, ExperimentRun, quality gates, workflow UI.

## 4. Monorepo images

| Image | Path |
|-------|------|
| `edd-api:local` | `api/` |
| `edd-console:local` | `console/` |
| `edd-worker:local` | `worker/` |

## 5. Product boundary

**EDD owns:** EvalSpec, EvalCase, ExperimentRun, scaffold, quality gates, console workflow, Langfuse integration orchestration.

**Langfuse owns:** Trace storage, detailed debugging UI, score analytics, SDK ingestion.

**Do not build:** Langfuse clone, full dataset product, custom trace browser, real LLM calls in MVP.

## 6. Main user journey (demo)

1. Open console → Langfuse status  
2. Select/create EvalSpec  
3. Import trace or create EvalCase  
4. Run ExperimentRun for candidate (`prompt_v4`)  
5. Scaffold + mock judge → results  
6. Push scores to Langfuse (when enabled)  
7. Inspect failures → open trace in Langfuse  
8. Run quality gate → pass/fail for CI  

## 7. Data model (Postgres)

Tables: `eval_specs`, `eval_cases`, `experiment_runs`, `evaluation_results`, `quality_gate_results` — see Phase 1 migrations. All rows include `tenant_id`.

## 8. API prefix

`/v1` — health, eval-specs, eval-cases, experiment-runs, evaluation-results, quality-gates, integrations/langfuse.

## Implementation phases

### Phase 0 — Repo bootstrap ✅ (target)

- [x] Monorepo layout api / console / worker / deploy / scripts
- [x] `/v1/health`, `/v1/ready`
- [x] Streamlit Overview + API health
- [x] Dockerfiles + compose + `build_images.sh` + `local_e2e.sh`
- [x] `git init` + remote (user)

**Validation:** `./scripts/local_e2e.sh`, `curl /v1/health`, open :8501

---

### Phase 0.5 — Platform import (from starter repos) ✅ (target)

Port **platform spine only** from `llm-evaluation-service-starter`, `llm-evaluation-console`, and `llm-evaluation-service-deploy`. Do **not** copy the evaluation-job domain (`POST /v1/evaluations`, `evaluation_jobs` table, job queue/worker loop).

**Import:**

- [x] API: auth, config, errors, JSON logging, OTel, Prometheus metrics, CORS, request IDs, storage factory (memory + Postgres health), Alembic wiring
- [x] Console: bearer auth UX, API client, Operations metrics page
- [x] Worker: logging + OTel shell (experiment jobs land in Phase 2)
- [x] Deploy: compose auth env, `local_e2e.sh --postgres`, demo JWT script, Helm chart skeleton
- [x] CI: API tests + Ruff (monorepo)

**Do not import:**

- Evaluation job routes, models, migrations, queue, or mock job evaluator
- Job-specific console tabs (Submit, Evaluations, Detail)

**Validation:**

```bash
./scripts/local_e2e.sh --postgres
curl -sf http://127.0.0.1:8000/v1/ready
curl -sf http://127.0.0.1:8000/metrics | head
# paste demo JWT into console sidebar → Overview + Operations load
make test
```

---

### Phase 1 — Core data model ✅ (target)

- [x] SQLAlchemy + Alembic + repositories
- [x] CRUD `/v1/eval-specs`, `/v1/eval-cases`
- [x] Demo JWT `RequestContext`, tenant-scoped queries
- [x] pytest CRUD + tenant isolation

**Validation:** create spec → create case → list by tenant

---

### Phase 2 — Experiment runs + mock evaluation ✅ (target)

- [x] `ExperimentRun`, `EvaluationResult` APIs
- [x] `scaffold_runner` + mock evaluator (deterministic)
- [x] Run summary: pass rate, avg score
- [x] `seed_demo_data.py`

**Validation:** POST experiment-runs → GET summary → deterministic scores

---

### Phase 3 — Console MVP ✅ (target)

- [x] Pages: Overview, Eval Specs, Eval Cases, Runs, Results Explorer, Quality Gates (placeholder), Langfuse (placeholder)
- [x] Full EDD loop in UI without curl

**Validation:**

```bash
./scripts/local_e2e.sh
# open console → create spec → case → run → view results on Results Explorer
make test
```

---

### Phase 4 — Langfuse adapter ✅ (target)

- [x] `LangfuseClientAdapter` only in `integrations/`
- [x] `LANGFUSE_ENABLED` — app works when false
- [x] `/v1/integrations/langfuse/health`
- [x] `docker-compose.langfuse.yml` (real stack)

**Validation:**

```bash
curl -sf http://127.0.0.1:8000/v1/integrations/langfuse/health
# optional overlay:
cd deploy && docker compose -f docker-compose.yml -f docker-compose.langfuse.yml up -d
make test
```

---

### Phase 5 — Push scores to Langfuse ✅ (target)

- [x] Score on result creation; store Langfuse refs
- [x] Metrics: push success/failure
- [x] Console link to trace (Results Explorer)

---

### Phase 6 — Import trace as EvalCase ✅ (target)

- [x] `GET trace`, `POST import-case`
- [x] Console: paste trace id → preview → save

---

### Phase 7 — Quality gates ✅ (target)

- [x] Threshold evaluation from EvalSpec (`GET /v1/experiment-runs/{id}/gate`)
- [x] Ingested runs reuse publish-time gate metadata
- [x] `scripts/run_quality_gate.sh` exit non-zero on fail
- [x] Console Quality Gates page
- [x] CI example in `docs/QUALITY_GATE_CI.md`

**Extension (lab integration):**

- [x] Generic external run ingest: `POST /v1/integrations/runs/publish`
- [x] Legacy alias: `POST /v1/integrations/lab/publish`
- [x] Persisted `ExperimentRun.ingest` provenance + `ingest_source` list filter

---

### Phase 8 — Polish + demo (in progress)

- [x] `docs/DEMO_SCRIPT.md`
- [x] Alembic migration for `experiment_runs.ingest`
- [ ] Architecture diagram refresh in README
- [ ] Helm chart skeleton polish

## MVP definition of done

- One-command local run  
- Create spec/case, run experiment, see results  
- Optional Langfuse connect + score push + trace import  
- Quality gate script  
- README tells the story  

## Non-goals

No Langfuse clone, no real LLM API in MVP, no agent framework, no sensitive text in metric labels.

## Cursor execution order

1. Phase 0 → 0.5 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8  
2. Small commits, tests green each phase  
3. Langfuse optional until Phase 4  

## Relationship to llm-evaluation-service-starter

That repo is a **job-evaluation starter**. This repo is a **new product**. Phase 0.5 imports its **platform spine** (auth, metrics, compose, local_e2e, Helm patterns). Do not fork the evaluation-job domain model — EDD tables and routes are built in Phases 1+.
