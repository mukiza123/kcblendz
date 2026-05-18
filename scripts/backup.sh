#!/usr/bin/env bash
# scripts/backup.sh — snapshot the SQLite DB into ./backups/ with a timestamp
set -euo pipefail

DB_PATH="${KCB_DB_PATH:-kcblendz.db}"
BACKUP_DIR="${BACKUP_DIR:-backups}"
mkdir -p "$BACKUP_DIR"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="${BACKUP_DIR}/kcblendz-${STAMP}.db"

if [ ! -f "$DB_PATH" ]; then
  echo "[backup] source DB not found at $DB_PATH" >&2
  exit 1
fi

# .backup is atomic — preferred over a plain cp on a running DB
sqlite3 "$DB_PATH" ".backup '${TARGET}'"
gzip -f "$TARGET"
echo "[backup] wrote ${TARGET}.gz"

# Retention: keep the last 14 daily backups
ls -1t "${BACKUP_DIR}"/*.db.gz 2>/dev/null | tail -n +15 | xargs -r rm --
