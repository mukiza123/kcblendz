#!/usr/bin/env bash
# scripts/restore.sh — restore a gzipped backup over the live SQLite DB
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: scripts/restore.sh path/to/backup.db.gz" >&2
  exit 1
fi

SOURCE="$1"
DB_PATH="${KCB_DB_PATH:-kcblendz.db}"

if [ ! -f "$SOURCE" ]; then
  echo "[restore] backup not found: $SOURCE" >&2
  exit 1
fi

# Stash existing DB before overwriting
if [ -f "$DB_PATH" ]; then
  STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
  cp "$DB_PATH" "${DB_PATH}.before-restore-${STAMP}"
  echo "[restore] saved current DB -> ${DB_PATH}.before-restore-${STAMP}"
fi

gunzip -c "$SOURCE" > "$DB_PATH"
echo "[restore] restored from $SOURCE -> $DB_PATH"
