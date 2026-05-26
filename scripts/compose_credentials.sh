#!/usr/bin/env bash
# Print credentials and verify Langfuse for the Docker compose stack.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AUTH_SECRET="${APP_AUTH_DEMO_SECRET:-local-demo-secret}"
TENANT_ID="${LOCAL_E2E_TENANT_ID:-tenant-a}"
SUBJECT="${LOCAL_E2E_SUBJECT:-local-user}"
API_URL="${EDD_API_BASE_URL:-http://127.0.0.1:8000}"

echo "Stopping host API/console if local_e2e left them running..."
"${REPO_ROOT}/scripts/local_e2e.sh" --stop >/dev/null 2>&1 || true

echo
echo "Demo bearer token (paste into console sidebar):"
APP_AUTH_DEMO_SECRET="${AUTH_SECRET}" \
  uv run --directory "${REPO_ROOT}/api" python "${REPO_ROOT}/scripts/create_demo_jwt.py" \
  --tenant-id "${TENANT_ID}" --subject "${SUBJECT}"

echo
echo "Console sidebar settings for compose:"
echo "  API base URL: http://localhost:8000"
echo "  Bearer token: (token above)"
echo
echo "Langfuse UI: http://localhost:3001"
echo "  login: admin@local.dev / local-demo-password"
echo

if curl -sf "${API_URL}/v1/health" >/dev/null 2>&1; then
  echo "Langfuse health (via ${API_URL}):"
  curl -sf "${API_URL}/v1/integrations/langfuse/health" || true
  echo
else
  for _ in $(seq 1 15); do
    if curl -sf "${API_URL}/v1/health" >/dev/null 2>&1; then
      echo "Langfuse health (via ${API_URL}):"
      curl -sf "${API_URL}/v1/integrations/langfuse/health" || true
      echo
      break
    fi
    sleep 2
  done
fi

if ! curl -sf "${API_URL}/v1/health" >/dev/null 2>&1; then
  echo "Could not reach the API at ${API_URL}."
  echo "If you just ran compose_up_langfuse.sh, wait ~1 minute and retry:"
  echo "  ./scripts/compose_credentials.sh"
  echo
  echo "If Docker is down, restart Colima first:"
  echo "  colima start"
fi
