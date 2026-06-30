#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

export BAR_PROJECT_DIR="${BAR_PROJECT_DIR:-$PROJECT_DIR}"
export BAR_VENV_DIR="${BAR_VENV_DIR:-$PROJECT_DIR/.venv}"
export BAR_ENV_FILE="${BAR_ENV_FILE:-$PROJECT_DIR/deploy/.env.deploy}"

exec /bin/bash "$SCRIPT_DIR/gunicorn_start.sh"