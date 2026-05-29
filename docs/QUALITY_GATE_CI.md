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

## Local script

```bash
./scripts/run_quality_gate.sh <experiment_run_id>
# exit 0 = pass, 1 = fail, 2 = no runs found
```

Environment:

- `EDD_API_BASE_URL` (default `http://127.0.0.1:8000`)
- `EDD_TENANT_ID` (default `tenant-a`)

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
