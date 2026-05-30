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
#   EDD_API_KEY       bearer token when platform auth is enabled
#   EDD_TOKEN_FILE    fallback token file (e.g. from local_e2e.sh)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_BASE="${EDD_API_BASE_URL:-http://127.0.0.1:8000}"
TENANT_ID="${EDD_TENANT_ID:-tenant-a}"
RUN_ID="${1:-}"

resolve_bearer_token() {
  if [[ -n "${EDD_API_KEY:-}" ]]; then
    printf '%s' "${EDD_API_KEY}"
    return 0
  fi
  local token_file="${EDD_TOKEN_FILE:-${TMPDIR:-/tmp}/edd-api.token}"
  if [[ -f "${token_file}" ]]; then
    tr -d '[:space:]' <"${token_file}"
    return 0
  fi
  if [[ -f "${REPO_ROOT}/api/pyproject.toml" ]]; then
    local minted
    minted="$(
      cd "${REPO_ROOT}/api"
      uv run python ../scripts/create_demo_jwt.py --tenant-id "${TENANT_ID}" --subject quality-gate 2>/dev/null
    )"
    if [[ -n "${minted}" ]]; then
      printf '%s' "${minted}"
      return 0
    fi
  fi
}

BEARER_TOKEN="$(resolve_bearer_token || true)"

curl_auth_args=()
gate_query_args=()
if [[ -n "${BEARER_TOKEN}" ]]; then
  curl_auth_args=(-H "Authorization: Bearer ${BEARER_TOKEN}")
else
  gate_query_args=(--data-urlencode "tenant_id=${TENANT_ID}")
fi

if [[ -z "${RUN_ID}" ]]; then
  if [[ -n "${BEARER_TOKEN}" ]]; then
    RUN_ID="$(curl -sf "${curl_auth_args[@]}" "${API_BASE}/v1/experiment-runs?limit=1" \
      | python3 -c "import json,sys; runs=json.load(sys.stdin).get('experiment_runs',[]); print(runs[0]['experiment_run_id'] if runs else '')")"
  else
    RUN_ID="$(curl -sf "${API_BASE}/v1/experiment-runs?tenant_id=${TENANT_ID}&limit=1" \
      | python3 -c "import json,sys; runs=json.load(sys.stdin).get('experiment_runs',[]); print(runs[0]['experiment_run_id'] if runs else '')")"
  fi
fi

if [[ -z "${RUN_ID}" ]]; then
  echo "No experiment runs found for tenant ${TENANT_ID}." >&2
  exit 2
fi

if [[ -n "${BEARER_TOKEN}" ]]; then
  response="$(curl -sf "${curl_auth_args[@]}" "${API_BASE}/v1/experiment-runs/${RUN_ID}/gate")"
else
  response="$(curl -sf -G "${API_BASE}/v1/experiment-runs/${RUN_ID}/gate" "${gate_query_args[@]}")"
fi

gate_status="$(python3 -c "import json,sys; print(json.load(sys.stdin)['gate_status'])" <<<"${response}")"
explanation="$(python3 -c "import json,sys; print(json.load(sys.stdin)['gate_explanation'])" <<<"${response}")"

echo "run_id=${RUN_ID}"
echo "gate_status=${gate_status}"
echo "explanation=${explanation}"

if [[ "${gate_status}" == "pass" ]]; then
  exit 0
fi

exit 1
