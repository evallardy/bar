#!/bin/bash
set -e

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${BAR_PROJECT_DIR:-$(cd -- "$SCRIPT_DIR/.." && pwd)}"
VENV_DIR="${BAR_VENV_DIR:-$PROJECT_DIR/.venv}"

if [ -n "${BAR_ENV_FILE:-}" ]; then
  ENV_FILE="$BAR_ENV_FILE"
elif [ -f "$PROJECT_DIR/deploy/.env.deploy" ]; then
  ENV_FILE="$PROJECT_DIR/deploy/.env.deploy"
else
  ENV_FILE="/etc/bar/bar.env"
fi

GUNICORN_CONFIG="${BAR_GUNICORN_CONFIG:-$PROJECT_DIR/deploy/gunicorn.conf.py}"
GUNICORN_APP="${BAR_GUNICORN_APP:-bar.wsgi:application}"

cd "$PROJECT_DIR"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-bar.settings_prod}

exec "$VENV_DIR/bin/gunicorn" \
  --config "$GUNICORN_CONFIG" \
  "$GUNICORN_APP"
