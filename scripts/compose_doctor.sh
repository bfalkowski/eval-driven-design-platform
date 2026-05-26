#!/usr/bin/env bash
# Quick diagnostics when localhost:8000 is silent or the console cannot connect.
set -u

API_URL="${EDD_API_BASE_URL:-http://127.0.0.1:8000}"

echo "=== Docker ==="
if ! docker info >/dev/null 2>&1; then
  echo "Docker is not reachable. Run:"
  echo "  colima stop && colima start"
  exit 1
fi

docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'deploy-edd|deploy-postgres|deploy-langfuse-web|NAMES' || true

echo
echo "=== Port 8000 ==="
lsof -iTCP:8000 -sTCP:LISTEN 2>/dev/null || echo "Nothing listening on 8000"

echo
echo "=== API health ==="
if curl -sf --max-time 5 "${API_URL}/v1/health"; then
  echo
  echo
  echo "=== Langfuse health ==="
  curl -sf --max-time 5 "${API_URL}/v1/integrations/langfuse/health" || true
  echo
else
  echo "FAILED: ${API_URL}/v1/health"
  echo
  echo "=== deploy-edd-api-1 logs (last 30 lines) ==="
  docker logs deploy-edd-api-1 --tail 30 2>&1 || true
  echo
  echo "=== deploy-edd-migrate logs ==="
  docker logs deploy-edd-migrate-1 2>&1 || docker compose -f deploy/docker-compose.yml logs edd-migrate 2>&1 | tail -20 || true
  echo
  echo "Try:"
  echo "  cd ~/Documents/repo/eval-driven-design-platform/deploy"
  echo "  docker compose -f docker-compose.yml -f docker-compose.langfuse.yml up -d edd-migrate edd-api"
  echo "  docker logs deploy-edd-api-1 --tail 30"
fi

echo
echo "=== Console ==="
curl -sf --max-time 3 http://127.0.0.1:8501/_stcore/health >/dev/null && echo "Console OK at http://localhost:8501" || echo "Console not reachable on 8501"
