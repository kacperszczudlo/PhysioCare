#!/usr/bin/env bash
# Reset dev database and apply fresh migrations.
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

echo "Dropping database ${POSTGRES_DB}..."
if ! dropdb --if-exists -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" "$POSTGRES_DB" 2>/dev/null; then
  echo "Warning: could not drop database (may be in use)."
fi

echo "Creating database ${POSTGRES_DB}..."
if ! createdb -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" "$POSTGRES_DB" 2>/dev/null; then
  echo "Error: could not create database. Run: sudo bash scripts/setup-postgres-auth.sh"
  exit 1
fi

echo "Running migrations..."
cd backend/physiocare
python manage.py migrate --noinput

echo "Done."
