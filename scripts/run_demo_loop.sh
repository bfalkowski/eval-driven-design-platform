#!/usr/bin/env bash
# Automate DEMO_SCRIPT.md API steps against a running platform API.
#
# Usage:
#   ./scripts/run_demo_loop.sh
#   EDD_API_KEY=<jwt> ./scripts/run_demo_loop.sh
#   RUN_DEMO_LAB_SMOKE=1 ./scripts/run_demo_loop.sh
#
# Env:
#   EDD_API_BASE_URL  (default http://127.0.0.1:8000)
#   EDD_TENANT_ID     (default tenant-a)
#   EDD_API_KEY       bearer token when auth enabled
#   EDD_TOKEN_FILE    default ${TMPDIR}/edd-api.token from local_e2e.sh
#   RUN_DEMO_LAB_SMOKE  set to 1 to run edd-agent-lab publish smoke when present

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}/api"
exec uv run python ../scripts/run_demo_loop.py
