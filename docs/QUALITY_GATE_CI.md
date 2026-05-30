# Quality Gate CI Integration

The platform exposes a unified gate evaluation for any experiment run:

```http
GET /v1/experiment-runs/{experiment_run_id}/gate?tenant_id=tenant-a
```

Response fields:

| Field | Meaning |
|-------|---------|
| `gate_status` | `pass`, `fail`, or `insufficient_evidence` |
| `gate_explanation` | Human-readable reason |
| `evaluation_source` | `ingest` (external publish) or `experiment_results` (platform mock eval) |
| `pass_threshold` | From EvalSpec |
| `average_score` | Platform avg score or ingest `overall_score` |

When `APP_AUTH_ENABLED=true` (default in `./scripts/local_e2e.sh`), pass a bearer token:

```bash
curl -sf "$EDD_API_BASE_URL/v1/experiment-runs/$RUN_ID/gate" \
  -H "Authorization: Bearer $EDD_API_KEY"
```

Or use tenant query param when auth is disabled: `?tenant_id=tenant-a`.

## Local script

```bash
./scripts/run_quality_gate.sh <experiment_run_id>
# exit 0 = pass, 1 = fail, 2 = no runs found
```

Environment:

- `EDD_API_BASE_URL` (default `http://127.0.0.1:8000`)
- `EDD_TENANT_ID` (default `tenant-a`)
- `EDD_API_KEY` or `EDD_TOKEN_FILE` when auth is enabled (see `./scripts/local_e2e.sh`)

## Automated demo loop

The platform repo includes a script that mirrors the API portion of `docs/DEMO_SCRIPT.md`:

```bash
./scripts/run_demo_loop.sh
./scripts/verify_demo.sh --postgres
```

GitHub Actions job **`demo-loop-api`** (in `.github/workflows/ci.yml`) starts the API with
auth enabled and runs `run_demo_loop.sh` on every pull request after unit tests pass.

Job **`integration-lab-smoke`** checks out **edd-agent-lab**, starts the platform API
(auth disabled, memory backend), and runs `edd-agent-lab/scripts/test_platform_publish.sh`.

## CI invariants (no AI provider keys)

GitHub Actions workflows intentionally **do not** receive model-provider API keys.

All required jobs — unit tests, `demo-loop-api`, `integration-lab-smoke`, container builds — must pass using:

- deterministic mock evaluation on the platform
- mock/local tools and fixtures in the lab
- platform bearer auth only where needed (`EDD_API_KEY` minted in CI; not an OpenAI key)

Live LLM or live provider calls belong behind an **explicit opt-in flag** for local or nightly runs only. When credentials are missing, code must skip live mode or fall back to mock automatically — never fail CI for absent provider keys.

See `AGENTS.md` in each repo for the agent-facing rule.

## GitHub Actions example

After publishing or creating a run in CI, fail the job when the gate does not pass:

```yaml
name: AI quality gate

on:
  pull_request:

jobs:
  eval-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - name: Wait for EDD API
        run: |
          for i in $(seq 1 30); do
            curl -sf "${EDD_API_BASE_URL}/v1/health" && exit 0
            sleep 2
          done
          exit 1
        env:
          EDD_API_BASE_URL: http://127.0.0.1:8000

      - name: Run quality gate
        run: ./scripts/run_quality_gate.sh "${EXPERIMENT_RUN_ID}"
        env:
          EDD_API_BASE_URL: http://127.0.0.1:8000
          EDD_TENANT_ID: tenant-a
          EXPERIMENT_RUN_ID: ${{ vars.LATEST_EXPERIMENT_RUN_ID }}
```

For lab publish flows, set `EXPERIMENT_RUN_ID` from the publish response (`platform_run_id`).

Ingested runs reuse gate results computed at publish time; platform runs evaluate average score against the EvalSpec threshold.
