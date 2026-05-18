#!/usr/bin/env bash
# scripts/dev.sh — local development server with auto-reload
set -euo pipefail

if [ ! -d ".venv" ]; then
  py -m venv .venv
fi
source .venv/bin/activate

pip install -q -r requirements.txt

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  echo "[dev] copied .env.example -> .env"
fi

export FLASK_APP=app
export FLASK_DEBUG=1
flask --app app init-db || true

exec py app.py
