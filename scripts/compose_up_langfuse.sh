#!/usr/bin/env bash
# Start the full EDD + Langfuse compose stack with a clean Langfuse seed.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY_DIR="${REPO_ROOT}/deploy"

if ! docker info >/dev/null 2>&1; then
  echo "Docker is not reachable. Starting Colima..." >&2
  if command -v colima >/dev/null 2>&1; then
    colima start || colima restart
    docker context use colima >/dev/null 2>&1 || true
  else
    echo "Install/start Docker Desktop or Colima, then retry." >&2
    exit 1
  fi
fi

echo "Stopping host API/console if running..."
"${REPO_ROOT}/scripts/local_e2e.sh" --stop >/dev/null 2>&1 || true

cd "${DEPLOY_DIR}"

echo "Resetting Langfuse Postgres (one-time seed for demo API keys)..."
docker compose -f docker-compose.yml -f docker-compose.langfuse.yml stop \
  langfuse-web langfuse-worker langfuse-postgres >/dev/null 2>&1 || true
docker compose -f docker-compose.yml -f docker-compose.langfuse.yml rm -f langfuse-postgres >/dev/null 2>&1 || true
docker volume rm deploy_langfuse-postgres-data >/dev/null 2>&1 || true

echo "Starting stack..."
docker compose -f docker-compose.yml -f docker-compose.langfuse.yml up -d

echo "Waiting for Langfuse..."
for _ in $(seq 1 60); do
  if docker run --rm --network deploy_default curlimages/curl:8.5.0 -sf \
    http://langfuse-web:3000/api/public/health >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "Waiting for EDD API..."
for _ in $(seq 1 60); do
  if curl -sf --max-time 2 http://127.0.0.1:8000/v1/health >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "Clearing stale Langfuse Redis auth cache..."
if docker exec deploy-langfuse-redis-1 redis-cli -a myredissecret FLUSHALL >/dev/null 2>&1; then
  echo "Redis cache cleared."
else
  echo "Skipped Redis flush (container not ready yet)."
fi

echo
echo "Stack started. Open:"
echo "  Console:  http://localhost:8501"
echo "  Langfuse: http://localhost:3001"
echo
"${REPO_ROOT}/scripts/compose_credentials.sh"
