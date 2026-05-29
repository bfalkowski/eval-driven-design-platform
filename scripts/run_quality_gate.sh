#!/usr/bin/env bash
# Evaluate quality gate for an experiment run (exit 0 on pass, 1 otherwise).
#
# Usage:
#   ./scripts/run_quality_gate.sh <experiment_run_id>
#   ./scripts/run_quality_gate.sh   # uses latest run for tenant
#
# Env:
#   EDD_API_BASE_URL  (default http://127.0.0.1:8000)
#   EDD_TENANT_ID     (default tenant-a)

set -euo pipefail

API_BASE="${EDD_API_BASE_URL:-http://127.0.0.1:8000}"
TENANT_ID="${EDD_TENANT_ID:-tenant-a}"
RUN_ID="${1:-}"

if [[ -z "${RUN_ID}" ]]; then
  RUN_ID="$(curl -sf "${API_BASE}/v1/experiment-runs?tenant_id=${TENANT_ID}&limit=1" \
    | python3 -c "import json,sys; runs=json.load(sys.stdin).get('experiment_runs',[]); print(runs[0]['experiment_run_id'] if runs else '')")"
fi

if [[ -z "${RUN_ID}" ]]; then
  echo "No experiment runs found for tenant ${TENANT_ID}." >&2
  exit 2
fi

response="$(curl -sf "${API_BASE}/v1/experiment-runs/${RUN_ID}/gate?tenant_id=${TENANT_ID}")"
gate_status="$(python3 -c "import json,sys; print(json.load(sys.stdin)['gate_status'])" <<<"${response}")"
explanation="$(python3 -c "import json,sys; print(json.load(sys.stdin)['gate_explanation'])" <<<"${response}")"

echo "run_id=${RUN_ID}"
echo "gate_status=${gate_status}"
echo "explanation=${explanation}"

if [[ "${gate_status}" == "pass" ]]; then
  exit 0
fi

exit 1
