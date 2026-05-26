#!/usr/bin/env bash
# Recover when `colima start` says running but `docker ps` fails.
set -euo pipefail

if ! command -v colima >/dev/null 2>&1; then
  echo "Colima is not installed. Install Colima or Docker Desktop." >&2
  exit 1
fi

echo "Restarting Colima (stop + start)..."
colima stop
colima start
docker context use colima >/dev/null 2>&1 || true

echo "Waiting for Docker..."
for _ in $(seq 1 30); do
  if docker info >/dev/null 2>&1; then
    echo "Docker is ready."
    docker ps --format 'table {{.Names}}\t{{.Status}}' | head -10
    exit 0
  fi
  sleep 1
done

echo "Docker still unavailable after Colima restart." >&2
echo "Try: colima delete && colima start --runtime docker" >&2
exit 1
