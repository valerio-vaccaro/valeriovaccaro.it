#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
elif [[ -f "venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "venv/bin/activate"
else
  echo "Error: no virtualenv found (.venv or venv)."
  echo "Create one with: python3 -m venv .venv"
  exit 1
fi

export FLASK_APP="run.py"
export FLASK_ENV="${FLASK_ENV:-development}"
export FLASK_DEBUG="${FLASK_DEBUG:-1}"

exec python -m flask run --host "${FLASK_HOST:-127.0.0.1}" --port "${FLASK_PORT:-5252}"
