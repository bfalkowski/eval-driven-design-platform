#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Building edd-api:local..."
docker build -t edd-api:local "${REPO_ROOT}/api"

echo "Building edd-console:local..."
docker build -f "${REPO_ROOT}/console/Dockerfile" -t edd-console:local "${REPO_ROOT}"

echo "Building edd-worker:local..."
docker build -t edd-worker:local "${REPO_ROOT}/worker"

echo "Done."
