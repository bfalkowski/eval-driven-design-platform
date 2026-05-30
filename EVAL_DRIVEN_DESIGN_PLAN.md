# Eval Driven Design Platform — Build Plan

Canonical **platform MVP** delivery plan for this monorepo. Build **phase by phase**; do not skip validation.

**Document hierarchy:**

| Doc | Scope |
|---|---|
| **This file** | What is built in **eval-driven-design-platform** (Phases 0–8 MVP + post-MVP roadmap) |
| [`docs/hld/`](docs/hld/README.md) | **EDD stack** intent, domain model, workflow, tool feasibility, reference scenario |
| [`docs/PRODUCT_VISION.md`](docs/PRODUCT_VISION.md) | Historical notes + optional future workloads (not canonical) |
| **edd-agent-lab** (separate repo) | Runnable agents, local evals, publish to platform |

Do not implement later HLD milestones while earlier platform validation is incomplete.

Optional local detail (not in git): `.local/PRODUCT_SPEC_REFERENCE.md` — original long-form spec (UI pages, SQL, payloads).

## 1. Product summary

**Eval Driven Design (EDD)** combines:

- Deterministic application scaffolding
- Langfuse-backed traces and scores
- Reusable eval cases and versioned eval specs
- Experiment runs across candidate prompts/models/workflows
- CI-style quality gates

**One line:** A lightweight eval-driven design control plane on Langfuse — observe traces, convert failures into eval cases, run candidates, score results, enforce gates before shipping AI changes.

**EDD stack:** This repo is the platform control plane. **[edd-agent-lab](https://github.com/bfalkowski/edd-agent-lab)** owns runnable agents and publishes runs via `POST /v1/integrations/runs/publish`. See [HLD-001](docs/hld/HLD-001-product-intent-and-system-boundaries.md).

## 2. Design principle

The **evaluated workflow** is the product boundary — not the LLM call.

Answer: *Given this task, eval spec, case set, scaffold, candidate version, and judge config — is this workflow good enough to ship?*

## 3. Architecture

```text
Operator → Streamlit Console (:8501) → FastAPI Control Plane (:8000) → Postgres
                                              ↓
                                    Worker / Evaluator (shell)
                                    scaffold + mock judge in API today
                                              ↓
                                    Langfuse Adapter (optional)

edd-agent-lab (:8502 / CLI) ──HTTP publish──► POST /v1/integrations/runs/publish
     (separate repo; platform must not depend on lab)
```

Langfuse: trace inspection, observations, score analytics.  
Platform: EvalSpec, EvalCase, ExperimentRun, quality gates, ingest provenance, workflow UI.

## 4. Monorepo images

| Image | Path |
|-------|------|
| `edd-api:local` | `api/` |
| `edd-console:local` | `console/` |
| `edd-worker:local` | `worker/` |

## 5. Product boundary

**Platform owns:** EvalSpec, EvalCase, ExperimentRun, scaffold, quality gates, external run ingest, console workflow, Langfuse integration orchestration.

**edd-agent-lab owns:** LangGraph agents, local eval suites, mock tools, lab-run artifacts, side-by-side dev console. Publishes to platform; must not be imported by platform.

**Langfuse owns:** Trace storage, detailed debugging UI, score analytics, SDK ingestion.

**Do not build:** Langfuse clone, full dataset product, custom trace browser, embedded agent runtime in this monorepo.

## 6. Main user journey (demo)

1. Open console → Langfuse status  
2. Select/create EvalSpec  
3. Import trace or create EvalCase  
4. Run ExperimentRun for candidate (`prompt_v4`)  
5. Scaffold + mock judge → results  
6. Push scores to Langfuse (when enabled)  
7. Inspect failures → open trace in Langfuse  
8. Run quality gate → pass/fail for CI  
9. *(Optional)* Publish run from **edd-agent-lab** → filter Runs by ingest source → gate on ingested run  

See `docs/DEMO_SCRIPT.md` and edd-agent-lab `scripts/test_platform_publish.sh`.

## 7. Data model (Postgres)

**Shipped (MVP):** `eval_specs`, `eval_cases`, `experiment_runs` (with optional `ingest` JSON), `evaluation_results` — see Alembic migrations. All rows include `tenant_id`.

**Target (HLD-002):** Agent, AgentTarget, BehaviorRule, EvalContract, tool requirements/feasibility, FailurePacket, FixPlan, PromotionRecord, etc. Evolve from EvalSpec/ingest blobs; see [HLD-002](docs/hld/HLD-002-domain-object-model.md).

## 8. API prefix

`/v1` — health, eval-specs, eval-cases, experiment-runs, evaluation-results, quality-gates, integrations/langfuse, **integrations/runs/publish** (legacy alias: integrations/lab/publish).

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

### Phase 8 — Polish + demo ✅ (MVP complete)

- [x] `docs/DEMO_SCRIPT.md`
- [x] `docs/QUALITY_GATE_CI.md`
- [x] Alembic migration for `experiment_runs.ingest`
- [x] `docs/hld/` — HLD-001 through HLD-005 (stack intent, domain, workflow, tools, reference scenario)
- [ ] Architecture diagram refresh in README — see [HLD-009](docs/hld/HLD-009-architecture-and-flow-diagrams.md) *(remaining polish)*
- [ ] Helm chart skeleton polish *(remaining polish)*

**Validation:** `./scripts/local_e2e.sh --postgres`, walk `docs/DEMO_SCRIPT.md`, lab `./scripts/test_platform_publish.sh` against local API.

---

## Post-MVP roadmap (HLD-aligned)

Build **after** Phase 8 validation. Follow [HLD-006](docs/hld/HLD-006-mvp-implementation-plan.md) milestones M2–M6 and [HLD-003](docs/hld/HLD-003-evaluation-driven-design-workflow.md) phase order.

### Phase 9 — Integration contract + CI harness

- [ ] Shared publish envelope fixtures (v1 today, v2 with `tool_bindings` / design IDs)
- [ ] Platform tests: ingest + gate response shape
- [ ] Lab tests: `publish.py` envelope matches fixtures
- [ ] Cross-repo CI: platform up → `test_platform_publish.sh` (auth-aware)

**Exit:** Lab publish seam protected in CI. See [HLD-007](docs/hld/HLD-007-platform-api-and-integration.md) (publish contract) and [HLD-006 Milestone 4](docs/hld/HLD-006-mvp-implementation-plan.md).

### Phase 10 — Design intent on platform

- [ ] Persist Agent, AgentTarget, BehaviorRule, EvalContract (extend or map from EvalSpec)
- [ ] Link ExperimentRun → target / contract / agent version IDs
- [ ] Console: Target, Rules, Eval Contract (read/edit; generation optional)

**Exit:** [HLD-005](docs/hld/HLD-005-reference-scenario-customer-escalation-triage.md) target/rules/contract registrable on platform.

### Phase 11 — Tool feasibility + readiness gates

- [ ] InformationRequirement, ToolRequirement, ToolFeasibilityReview (YAML artifact bridge OK)
- [ ] Extend QualityGateService: behavior vs tool vs production readiness
- [ ] Console: Information Requirements, Tool Requirements, Tool Feasibility

**Exit:** `pass_for_demo_not_production` from [HLD-004](docs/hld/HLD-004-tool-requirements-and-feasibility.md) and [HLD-012](docs/hld/HLD-012-versioning-gates-and-promotion.md) representable.

### Phase 12 — Evidence loop (failure → fix → compare)

- [ ] FailurePacket, FixPlan, Comparison as platform objects (normalize ingest blobs)
- [ ] TraceLink metadata; lab publishes structured failure/fix artifacts
- [ ] Console: Failure Packets, Fix Plans, Compare Versions

**Exit:** HLD-005 v0→v1 story navigable in platform UI. See [HLD-012](docs/hld/HLD-012-versioning-gates-and-promotion.md) comparison and gate artifacts.

### Phase 13 — Console lifecycle + lab reference scenario

- [ ] Console nav: Design / Build / Evaluate / Promote — see [HLD-011](docs/hld/HLD-011-console-information-architecture.md) (MVP subset)
- [ ] Lab: Customer Escalation Triage agent + mock data per HLD-005 *(or migrate from customer-solution)*

**Exit:** End-to-end demo matches HLD-005 acceptance criteria.

### Phase 14 — Operational mode *(defer)*

- [ ] OperationalRun, PromotionRecord persistence, Live Run / Action Queue — [HLD-012](docs/hld/HLD-012-versioning-gates-and-promotion.md)
- [ ] Approval-gated write tools

**Exit:** HLD-003 Phase 7 (Promote and Operate) — only after Phases 10–13 stable.

## MVP definition of done ✅

- [x] One-command local run  
- [x] Create spec/case, run experiment, see results  
- [x] Optional Langfuse connect + score push + trace import  
- [x] Quality gate script + console page  
- [x] External run ingest from edd-agent-lab  
- [x] README + DEMO_SCRIPT tell the story  
- [ ] Remaining: README diagram polish ([HLD-009](docs/hld/HLD-009-architecture-and-flow-diagrams.md)), cross-repo CI (Phase 9)

## Non-goals

No Langfuse clone, no sensitive text in metric labels, no agent implementation in this monorepo (use edd-agent-lab), no pretending mock tools are production-ready (HLD-004).

## Cursor execution order

**MVP (complete):** Phase 0 → 0.5 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8  

**Post-MVP:** Phase 9 → 10 → 11 → 12 → 13 → 14 — validate each phase before the next. Read relevant HLD before coding.

1. Small commits, tests green each phase  
2. Langfuse optional until Phase 4 (already satisfied)  
3. Keep v0.1.0-style ingest + gate path working while adding HLD domain objects

## Relationship to llm-evaluation-service-starter

That repo is a **job-evaluation starter**. This repo is a **new product**. Phase 0.5 imports its **platform spine** (auth, metrics, compose, local_e2e, Helm patterns). Do not fork the evaluation-job domain model — EDD tables and routes are built in Phases 1+.
