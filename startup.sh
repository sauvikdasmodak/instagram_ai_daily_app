#!/usr/bin/env bash
set -euo pipefail

export APP_HOST="${APP_HOST:-0.0.0.0}"
export APP_PORT="${PORT:-${WEBSITES_PORT:-${APP_PORT:-8000}}}"

echo "Starting Instagram AI Daily App on ${APP_HOST}:${APP_PORT}"
python app.py --host "${APP_HOST}" --port "${APP_PORT}"
