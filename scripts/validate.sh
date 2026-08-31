#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

uv run --locked python -m compileall -q src tests scripts tools
uv run --locked ruff check src tests scripts tools
uv run --locked pytest --cov --cov-report=term-missing
uv run --locked python scripts/build_site.py --check
uv run --locked python tools/repo_scan.py --pretty
uv run --locked python tools/history_scan.py --pretty
uv run --locked python tools/package_check.py
uv run --locked python tools/browser_check.py

VALIDATION_TMP="$(mktemp -d)"
SERVER_LOG="${VALIDATION_TMP}/server.log"
SERVER_PID=""

cleanup() {
  if [[ -n "${SERVER_PID}" ]]; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
  rm -rf -- "${VALIDATION_TMP}"
}
trap cleanup EXIT

MTS_DATABASE_PATH="${VALIDATION_TMP}/smoke.db" \
  uv run --locked marketplace-trust-starter \
  --host 127.0.0.1 \
  --port 8101 \
  >"${SERVER_LOG}" 2>&1 &
SERVER_PID=$!

uv run --locked python "${PROJECT_ROOT}/scripts/smoke_test.py" \
  --base-url "http://127.0.0.1:8101"

echo "Validation complete."
