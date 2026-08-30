#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Activate virtualenv if present
if [[ -f "${WORKSPACE_ROOT}/.venv/bin/activate" ]]; then
    source "${WORKSPACE_ROOT}/.venv/bin/activate"
fi

export PATH="${WORKSPACE_ROOT}/.venv/bin:${PATH}"

python3 "${SCRIPT_DIR}/run.py" "$@"
