#!/usr/bin/env bash

select_mts_python() {
  if [[ -n "${MTS_PYTHON:-}" ]]; then
    printf '%s\n' "${MTS_PYTHON}"
    return
  fi

  if [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
    printf '%s\n' "${PROJECT_ROOT}/.venv/bin/python"
    return
  fi

  if command -v mise >/dev/null 2>&1; then
    local mise_python
    if mise_python="$(mise x python@3.12 -- which python 2>/dev/null)" \
      && [[ -n "${mise_python}" ]]; then
      printf '%s\n' "${mise_python}"
      return
    fi
  fi

  local candidate
  for candidate in python3.13 python3.12 python3.11 python3; do
    if command -v "${candidate}" >/dev/null 2>&1 \
      && "${candidate}" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))' \
        >/dev/null 2>&1; then
      command -v "${candidate}"
      return
    fi
  done

  echo "Marketplace Trust Starter requires Python 3.11 or newer." >&2
  return 1
}
