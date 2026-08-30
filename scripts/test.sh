#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${PROJECT_ROOT}/scripts/python_runtime.sh"
PYTHON_BIN="$(select_mts_python)"

if ! "${PYTHON_BIN}" -c 'import pytest, fastapi, httpx' >/dev/null 2>&1; then
  echo "Development dependencies are missing. Install with:" >&2
  echo "  ${PYTHON_BIN} -m pip install -e '.[dev]'" >&2
  exit 1
fi

export PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
exec "${PYTHON_BIN}" -m pytest "$@"
