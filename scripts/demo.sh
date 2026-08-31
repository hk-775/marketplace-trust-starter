#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

if ! command -v uv >/dev/null 2>&1; then
  echo "Marketplace Trust Starter requires uv: https://docs.astral.sh/uv/" >&2
  exit 1
fi

uv sync --locked --no-dev --python "${MTS_PYTHON:-3.12}"

export MTS_HOST="${MTS_HOST:-127.0.0.1}"
export MTS_PORT="${MTS_PORT:-8101}"
export MTS_DATABASE_PATH="${MTS_DATABASE_PATH:-${PROJECT_ROOT}/data/marketplace_trust_starter.db}"

echo "Marketplace Trust Starter: http://${MTS_HOST}:${MTS_PORT}"
echo "Dashboard: http://${MTS_HOST}:${MTS_PORT}/dashboard"
echo "API docs: http://${MTS_HOST}:${MTS_PORT}/api/docs"

exec uv run --locked --no-dev marketplace-trust-starter \
  --host "${MTS_HOST}" \
  --port "${MTS_PORT}"
