#!/bin/bash
set -e

PROJECT_DIR="/srv/bar/app"
VENV_DIR="/srv/bar/app/.venv"
ENV_FILE="/etc/bar/bar.env"

cd "$PROJECT_DIR"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-bar.settings_prod}

exec "$VENV_DIR/bin/gunicorn" \
  --config "$PROJECT_DIR/deploy/gunicorn.conf.py" \
  bar.wsgi:application
