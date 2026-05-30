# EDD Platform Demo Script

Walk through the eval-driven design loop locally in ~15 minutes.

## Prerequisites

```bash
cd eval-driven-design-platform
cp .env.example .env
./scripts/local_e2e.sh --postgres
# Optional Langfuse overlay:
# ./scripts/local_e2e.sh --postgres --langfuse
```

Open the console at http://localhost:8501 and paste the demo JWT from the script output.

## 1. Observe (Overview)

- Confirm API health and Langfuse integration status on **Overview**.
- Note the workflow loop: Observe → Case → Run → Evaluate → Decide.

## 2. Define success (Eval Specs)

1. Go to **Eval Specs**.
2. Create a spec with rubric and pass threshold (e.g. 70).
3. Confirm it appears in the list.

## 3. Create cases (Eval Cases)

1. Go to **Eval Cases**.
2. Add a manual case tied to your spec.
3. *(Optional with Langfuse)* On **Langfuse**, paste a trace ID, preview, and import as EvalCase.

## 4. Run a candidate (Runs)

1. Go to **Runs**.
2. Select your spec and run `prompt_v4` against all cases.
3. Note pass rate, average score, and **gate** status on completion.
4. Review recent runs table (platform-native runs show `source=platform`).

## 5. Explore results (Results Explorer)

1. Select the run you just created.
2. Inspect per-case scores and judge breakdown.
3. With Langfuse enabled, open trace links for results that have trace IDs.

## 6. Quality gate (Quality Gates + CI)

1. Go to **Quality Gates** — review gate status for recent runs.
2. From the repo root:

```bash
./scripts/run_quality_gate.sh   # latest run for tenant-a
./scripts/run_quality_gate.sh <experiment_run_id>
```

Exit code `0` = pass, `1` = fail.

## 7. External ingest (edd-agent-lab, optional)

With the platform API running on `:8000` (from `./scripts/local_e2e.sh`, auth enabled by default):

```bash
cd ../edd-agent-lab
# Option A: smoke script (auto-mints JWT if platform repo is sibling)
./scripts/test_platform_publish.sh

# Option B: manual publish (paste JWT from local_e2e output into EDD_API_KEY)
EDD_CLIENT_MODE=http \
EDD_API_BASE_URL=http://127.0.0.1:8000 \
EDD_TENANT_ID=tenant-a \
EDD_EVAL_SPEC_ID=<your-spec-id> \
EDD_API_KEY=<demo-jwt-from-local_e2e> \
.venv/bin/edd-lab publish-run --agent customer-solution --version v1-discovery-graph
```

Expect `published_http` in CLI output. With auth disabled (`APP_AUTH_ENABLED=false`), omit `EDD_API_KEY` and pass `tenant_id` on the envelope only.

Back on the platform **Runs** page, filter by ingest source `edd-agent-lab` and inspect ingest provenance JSON.

## 8. Decide

- **Pass** — promote candidate or document baseline.
- **Fail** — add regression cases, iterate candidate, re-run.
- **Ingested runs** — gate reflects external eval summary and failure packets from the producer.

## Tear down

```bash
./scripts/local_e2e.sh --stop
```
