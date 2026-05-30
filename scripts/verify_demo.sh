#!/usr/bin/env bash
# Start local API, run automated demo loop, optionally lab publish smoke, then stop.
#
# Usage:
#   ./scripts/verify_demo.sh
#   ./scripts/verify_demo.sh --postgres
#   ./scripts/verify_demo.sh --postgres --lab-smoke
#
# Mirrors the API path in docs/DEMO_SCRIPT.md without manual console clicks.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
USE_POSTGRES=false
RUN_LAB_SMOKE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --postgres) USE_POSTGRES=true; shift ;;
    --lab-smoke) RUN_LAB_SMOKE=true; shift ;;
    -h|--help)
      sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

cleanup() {
  "${REPO_ROOT}/scripts/local_e2e.sh" --stop >/dev/null 2>&1 || true
}
trap cleanup EXIT

local_e2e_args=(--no-console --no-smoke)
if [[ "${USE_POSTGRES}" == "true" ]]; then
  local_e2e_args+=(--postgres)
fi

echo "Starting platform API..."
"${REPO_ROOT}/scripts/local_e2e.sh" "${local_e2e_args[@]}" >/dev/null

TOKEN_FILE="${EDD_TOKEN_FILE:-${TMPDIR:-/tmp}/edd-api.token}"
export EDD_TOKEN_FILE="${TOKEN_FILE}"
export EDD_API_BASE_URL="${EDD_API_BASE_URL:-http://127.0.0.1:8000}"
export EDD_TENANT_ID="${EDD_TENANT_ID:-tenant-a}"
if [[ "${RUN_LAB_SMOKE}" == "true" ]]; then
  export RUN_DEMO_LAB_SMOKE=1
fi

echo "Running automated demo loop..."
"${REPO_ROOT}/scripts/run_demo_loop.sh"

echo
echo "verify_demo.sh passed."
