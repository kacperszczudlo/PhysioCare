#!/usr/bin/env bash
# Regenerate database/schema.sql from the current PostgreSQL database.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

: "${POSTGRES_DB:?Set POSTGRES_DB in .env}"
: "${POSTGRES_USER:?Set POSTGRES_USER in .env}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export PGPASSWORD="${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}"

OUTPUT="$ROOT_DIR/database/schema.sql"
TMP="$(mktemp)"

pg_dump --schema-only --no-owner --no-privileges \
  -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" "$POSTGRES_DB" \
  > "$TMP"

{
  echo "-- PhysioCare — auto-generated from Django migrations"
  echo "-- Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "-- Do not edit manually. Run: ./scripts/sync-schema-sql.sh"
  echo ""
  cat "$TMP"
} > "$OUTPUT"

rm "$TMP"
echo "Wrote $OUTPUT"
