#!/usr/bin/env bash
# Verify lab publish fixture copies match platform contract fixtures.
#
# Usage:
#   ./scripts/check_publish_fixtures_sync.sh
#   EDD_LAB_ROOT=../edd-agent-lab ./scripts/check_publish_fixtures_sync.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAB_ROOT="${EDD_LAB_ROOT:-${REPO_ROOT}/../edd-agent-lab}"
PLATFORM_FIXTURES="${REPO_ROOT}/contracts/publish/v1"
LAB_FIXTURES="${LAB_ROOT}/tests/fixtures/publish/v1"

if [[ ! -d "${LAB_FIXTURES}" ]]; then
  echo "Lab fixtures directory not found: ${LAB_FIXTURES}" >&2
  exit 1
fi

shopt -s nullglob
platform_files=("${PLATFORM_FIXTURES}"/envelope-*.json)
if [[ ${#platform_files[@]} -eq 0 ]]; then
  echo "No platform envelope fixtures under ${PLATFORM_FIXTURES}" >&2
  exit 1
fi

for platform_file in "${platform_files[@]}"; do
  name="$(basename "${platform_file}")"
  lab_file="${LAB_FIXTURES}/${name}"
  if [[ ! -f "${lab_file}" ]]; then
    echo "Missing lab fixture copy: ${lab_file}" >&2
    exit 1
  fi
  if ! diff -q "${platform_file}" "${lab_file}" >/dev/null; then
    echo "Fixture drift: ${name}" >&2
    diff -u "${platform_file}" "${lab_file}" >&2 || true
    exit 1
  fi
done

echo "Publish fixtures in sync (${#platform_files[@]} envelope file(s))."
