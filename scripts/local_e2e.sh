#!/usr/bin/env bash
# Start EDD platform locally (host processes or docker compose).
#
#   ./scripts/local_e2e.sh              # API + console on host (memory backend)
#   ./scripts/local_e2e.sh --postgres   # docker Postgres + host API + migrations
#   ./scripts/local_e2e.sh --postgres --langfuse  # above + Langfuse overlay on :3001
#   ./scripts/local_e2e.sh --compose    # full stack via docker compose
#   ./scripts/local_e2e.sh --no-smoke   # start only
#   ./scripts/local_e2e.sh --stop

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PID_FILE="${TMPDIR:-/tmp}/edd-api.pid"
CONSOLE_PID_FILE="${TMPDIR:-/tmp}/edd-console.pid"
API_LOG="${TMPDIR:-/tmp}/edd-api.log"
CONSOLE_LOG="${TMPDIR:-/tmp}/edd-console.log"
TOKEN_FILE="${TMPDIR:-/tmp}/edd-api.token"
COMPOSE_MARKER="${TMPDIR:-/tmp}/edd-compose.marker"
DATABASE_URL="${LOCAL_E2E_DATABASE_URL:-postgresql+asyncpg://edd:edd@localhost:5433/edd}"

PORT="${LOCAL_E2E_PORT:-8000}"
CONSOLE_PORT="${LOCAL_E2E_CONSOLE_PORT:-8501}"
AUTH_SECRET="${APP_AUTH_DEMO_SECRET:-local-demo-secret}"
TENANT_ID="${LOCAL_E2E_TENANT_ID:-tenant-a}"
SUBJECT="${LOCAL_E2E_SUBJECT:-local-user}"
BASE_URL="http://127.0.0.1:${PORT}"
CONSOLE_URL="http://127.0.0.1:${CONSOLE_PORT}"

USE_POSTGRES=false
USE_LANGFUSE=false
RUN_SMOKE=true
START_CONSOLE=true
MODE="host"
ACTION="start"

usage() {
  sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
}

kill_port() {
  local port="$1"
  local pids
  pids="$(lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true)"
  [[ -z "${pids}" ]] && return 0
  kill -TERM ${pids} 2>/dev/null || true
  sleep 0.3
}

stop_pid_file() {
  local pid_file="$1"
  [[ -f "${pid_file}" ]] || return 0
  local old_pid
  old_pid="$(cat "${pid_file}")"
  if [[ -n "${old_pid}" ]] && kill -0 "${old_pid}" 2>/dev/null; then
    kill -TERM "${old_pid}" 2>/dev/null || true
    sleep 0.3
  fi
  rm -f "${pid_file}"
}

stop_host() {
  stop_pid_file "${API_PID_FILE}"
  stop_pid_file "${CONSOLE_PID_FILE}"
  kill_port "${PORT}"
  kill_port "${CONSOLE_PORT}"
  pkill -f "uvicorn app.main:app" 2>/dev/null || true
  pkill -f "streamlit run streamlit_app.py" 2>/dev/null || true
}

stop_compose() {
  if [[ -f "${COMPOSE_MARKER}" ]]; then
    cd "${REPO_ROOT}/deploy"
    docker compose down
    rm -f "${COMPOSE_MARKER}"
  fi
}

stop_all() {
  stop_host
  stop_compose
  rm -f "${TOKEN_FILE}"
  echo "Stopped."
}

wait_for_postgres() {
  local attempts=40
  local i
  cd "${REPO_ROOT}/deploy"
  for ((i = 1; i <= attempts; i++)); do
    if docker compose exec -T postgres pg_isready -U edd -d edd >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.5
  done
  echo "Postgres did not become ready." >&2
  return 1
}

start_postgres_compose() {
  cd "${REPO_ROOT}/deploy"
  docker compose up -d postgres
  echo "postgres" >"${COMPOSE_MARKER}"
  wait_for_postgres
}

start_langfuse_compose() {
  cd "${REPO_ROOT}/deploy"
  echo "Starting Langfuse overlay (UI on http://localhost:3001)..."
  docker compose -f docker-compose.yml -f docker-compose.langfuse.yml up -d \
    langfuse-postgres langfuse-redis langfuse-clickhouse langfuse-minio \
    langfuse-web langfuse-worker
  wait_for_langfuse
  if docker exec deploy-langfuse-redis-1 redis-cli -a myredissecret FLUSHALL >/dev/null 2>&1; then
    echo "Langfuse Redis cache cleared."
  fi
}

wait_for_langfuse() {
  local attempts=60
  local i
  for ((i = 1; i <= attempts; i++)); do
    if curl -sf http://127.0.0.1:3001/api/public/health >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "Langfuse did not become ready at http://localhost:3001" >&2
  return 1
}

run_migrations() {
  cd "${REPO_ROOT}/api"
  APP_DATABASE_URL="${DATABASE_URL}" uv run alembic upgrade head
}

wait_for_ready() {
  local attempts=40
  local i
  for ((i = 1; i <= attempts; i++)); do
    if curl -sf "${BASE_URL}/v1/ready" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
  done
  echo "API did not become ready at ${BASE_URL}/v1/ready" >&2
  tail -20 "${API_LOG}" >&2 || true
  return 1
}

wait_for_console() {
  local attempts=40
  local i
  for ((i = 1; i <= attempts; i++)); do
    if curl -sf "${CONSOLE_URL}/_stcore/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
  done
  echo "Console did not become ready at ${CONSOLE_URL}" >&2
  tail -20 "${CONSOLE_LOG}" >&2 || true
  return 1
}

create_demo_token() {
  cd "${REPO_ROOT}/api"
  APP_AUTH_DEMO_SECRET="${AUTH_SECRET}" \
    uv run python ../scripts/create_demo_jwt.py --tenant-id "${TENANT_ID}" --subject "${SUBJECT}"
}

start_api() {
  cd "${REPO_ROOT}/api"
  : >"${API_LOG}"
  local storage_backend="memory"
  local -a api_env=(
    "APP_AUTH_ENABLED=true"
    "APP_AUTH_DEMO_SECRET=${AUTH_SECRET}"
    "APP_OTEL_EXPORTER=none"
  )
  if [[ "${USE_POSTGRES}" == "true" ]]; then
    storage_backend="postgres"
    api_env+=(
      "APP_STORAGE_BACKEND=postgres"
      "APP_DATABASE_URL=${DATABASE_URL}"
      "APP_AUTO_CREATE_SCHEMA=false"
    )
  else
    api_env+=("APP_STORAGE_BACKEND=memory")
  fi
  if [[ "${USE_LANGFUSE}" == "true" ]]; then
    api_env+=(
      "APP_LANGFUSE_ENABLED=true"
      "APP_LANGFUSE_HOST=http://127.0.0.1:3001"
      "APP_LANGFUSE_PUBLIC_KEY=pk-lf-local-demo"
      "APP_LANGFUSE_SECRET_KEY=sk-lf-local-demo"
      "APP_LANGFUSE_PROJECT_NAME=local-demo"
    )
  fi
  echo "Starting API on ${BASE_URL} (${storage_backend})"
  env "${api_env[@]}" \
    nohup uv run uvicorn app.main:app --host 127.0.0.1 --port "${PORT}" >>"${API_LOG}" 2>&1 &
  echo $! >"${API_PID_FILE}"
  wait_for_ready
}

start_console() {
  local token="${1:-}"
  cd "${REPO_ROOT}/console"
  : >"${CONSOLE_LOG}"
  echo "Starting console on ${CONSOLE_URL}"
  EDD_API_BASE_URL="${BASE_URL}" \
    EDD_BEARER_TOKEN="${token}" \
    EDD_TOKEN_FILE="${TOKEN_FILE}" \
    PYTHONPATH="${REPO_ROOT}/console" \
    nohup uv run streamlit run streamlit_app.py \
      --server.headless true \
      --server.port "${CONSOLE_PORT}" \
      --server.address 127.0.0.1 >>"${CONSOLE_LOG}" 2>&1 &
  echo $! >"${CONSOLE_PID_FILE}"
  wait_for_console
}

run_smoke_test() {
  echo "=== health ==="
  curl -sf "${BASE_URL}/v1/health"
  echo
  echo "=== ready ==="
  curl -sf "${BASE_URL}/v1/ready"
  echo
  echo "=== metrics ==="
  curl -sf "${BASE_URL}/metrics" | head -5
  echo
}

print_urls() {
  local token="$1"
  echo
  echo "Console: ${CONSOLE_URL}"
  echo "API docs: ${BASE_URL}/docs"
  echo "Metrics: ${BASE_URL}/metrics"
  echo
  echo "Demo bearer token (auto-loaded by console, or paste + Apply credentials):"
  echo "${token}"
  echo "(saved to ${TOKEN_FILE}; console reads EDD_TOKEN_FILE on startup)"
  if [[ "${USE_POSTGRES}" == "true" ]]; then
    echo "Storage: Postgres on localhost:5433"
  else
    echo "Storage: in-memory"
  fi
  if [[ "${USE_LANGFUSE}" == "true" ]]; then
    echo "Langfuse: http://localhost:3001 (admin@local.dev / local-demo-password)"
  else
    echo "Langfuse: disabled (add --langfuse to enable)"
  fi
  echo "Stop: ./scripts/local_e2e.sh --stop"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --compose) MODE="compose"; shift ;;
    --postgres) USE_POSTGRES=true; shift ;;
    --langfuse) USE_LANGFUSE=true; shift ;;
    --no-smoke) RUN_SMOKE=false; shift ;;
    --no-console) START_CONSOLE=false; shift ;;
    --stop) ACTION="stop"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

if [[ "${ACTION}" == "stop" ]]; then
  stop_all
  exit 0
fi

stop_all

if [[ "${MODE}" == "compose" ]]; then
  cd "${REPO_ROOT}/deploy"
  docker compose up --build -d
  for _ in $(seq 1 40); do
    curl -sf http://127.0.0.1:8000/v1/health >/dev/null 2>&1 && break
    sleep 0.5
  done
  curl -sf http://127.0.0.1:8000/v1/health
  echo
  echo "Console: http://localhost:8501"
  exit 0
fi

if [[ "${USE_POSTGRES}" == "true" ]]; then
  start_postgres_compose
  run_migrations
fi

if [[ "${USE_LANGFUSE}" == "true" ]]; then
  start_langfuse_compose
fi

start_api
token="$(create_demo_token)"
printf '%s\n' "${token}" >"${TOKEN_FILE}"

if [[ "${START_CONSOLE}" == "true" ]]; then
  start_console "${token}"
fi

if [[ "${RUN_SMOKE}" == "true" ]]; then
  run_smoke_test
  if [[ "${USE_LANGFUSE}" == "true" ]]; then
    echo "=== langfuse health ==="
    curl -sf "${BASE_URL}/v1/integrations/langfuse/health"
    echo
  fi
  echo "Smoke test passed."
fi

print_urls "${token}"
