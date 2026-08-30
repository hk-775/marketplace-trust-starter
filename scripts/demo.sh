#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${PROJECT_ROOT}/scripts/python_runtime.sh"
PYTHON_BIN="$(select_mts_python)"

if ! "${PYTHON_BIN}" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'; then
  echo "Marketplace Trust Starter requires Python 3.11 or newer." >&2
  exit 1
fi

if ! "${PYTHON_BIN}" -c 'import fastapi, uvicorn' >/dev/null 2>&1; then
  VENV_DIR="${PROJECT_ROOT}/.venv"
  if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
  fi
  "${VENV_DIR}/bin/python" -m pip install --disable-pip-version-check -e "${PROJECT_ROOT}"
  PYTHON_BIN="${VENV_DIR}/bin/python"
fi

export PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
export MTS_HOST="${MTS_HOST:-127.0.0.1}"
export MTS_PORT="${MTS_PORT:-8101}"
export MTS_DATABASE_PATH="${MTS_DATABASE_PATH:-${PROJECT_ROOT}/data/marketplace_trust_starter.db}"

echo "Marketplace Trust Starter: http://${MTS_HOST}:${MTS_PORT}"
echo "Dashboard: http://${MTS_HOST}:${MTS_PORT}/dashboard"
echo "API docs: http://${MTS_HOST}:${MTS_PORT}/api/docs"

exec "${PYTHON_BIN}" -m marketplace_trust_starter \
  --host "${MTS_HOST}" \
  --port "${MTS_PORT}"
