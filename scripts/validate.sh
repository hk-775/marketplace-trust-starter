#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${PROJECT_ROOT}/scripts/python_runtime.sh"
PYTHON_BIN="$(select_mts_python)"

export PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

"${PYTHON_BIN}" -m compileall -q "${PROJECT_ROOT}/src" "${PROJECT_ROOT}/tests"
"${PYTHON_BIN}" -m pytest
"${PYTHON_BIN}" "${PROJECT_ROOT}/scripts/build_site.py" --check

if command -v ruff >/dev/null 2>&1; then
  ruff check "${PROJECT_ROOT}/src" "${PROJECT_ROOT}/tests" "${PROJECT_ROOT}/scripts"
fi

if rg -n "github\\.com/example|example\\.com/marketplace-trust-starter" \
  "${PROJECT_ROOT}" \
  -g '!*.db' \
  -g '!CHANGELOG.md'
then
  echo "Placeholder public URL found." >&2
  exit 1
fi

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
  "${PYTHON_BIN}" -m marketplace_trust_starter \
  --host 127.0.0.1 \
  --port 8101 \
  >"${SERVER_LOG}" 2>&1 &
SERVER_PID=$!

"${PYTHON_BIN}" "${PROJECT_ROOT}/scripts/smoke_test.py" \
  --base-url "http://127.0.0.1:8101"

echo "Validation complete."
