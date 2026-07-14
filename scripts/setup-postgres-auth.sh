#!/usr/bin/env bash
# PhysioCare — naprawa pg_hba.conf (tylko połączenia TCP dla pgAdmin)
# Uruchom: sudo bash scripts/setup-postgres-auth.sh
# Wymaga .env w katalogu głównym repozytorium (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Brak pliku ${ENV_FILE}."
  echo "Skopiuj: cp .env.example .env i uzupełnij POSTGRES_*."
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

: "${POSTGRES_USER:?Ustaw POSTGRES_USER w .env}"
: "${POSTGRES_PASSWORD:?Ustaw POSTGRES_PASSWORD w .env}"
: "${POSTGRES_DB:?Ustaw POSTGRES_DB w .env}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

sql_quote() {
  printf '%s' "$1" | sed "s/'/''/g"
}

PG_USER="$(sql_quote "${POSTGRES_USER}")"
PG_PASS="$(sql_quote "${POSTGRES_PASSWORD}")"
PG_DB="$(sql_quote "${POSTGRES_DB}")"

PG_HBA="/var/lib/pgsql/data/pg_hba.conf"
BACKUP="${PG_HBA}.bak.$(date +%Y%m%d-%H%M%S)"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Uruchom: sudo bash scripts/setup-postgres-auth.sh"
  exit 1
fi

if [[ ! -f "${PG_HBA}" ]]; then
  echo "Nie znaleziono ${PG_HBA}"
  exit 1
fi

# Przywróć backup jeśli poprzedni skrypt zepsuł local peer
LATEST_BACKUP="$(ls -t "${PG_HBA}.bak."* 2>/dev/null | head -1 || true)"
if [[ -n "${LATEST_BACKUP}" ]]; then
  echo "==> Przywracam backup: ${LATEST_BACKUP}"
  cp "${LATEST_BACKUP}" "${PG_HBA}"
fi

echo "==> Nowa kopia zapasowa: ${BACKUP}"
cp "${PG_HBA}" "${BACKUP}"

echo "==> Zmiana TYLKO host 127.0.0.1 / ::1: ident -> scram-sha-256"
echo "    (local peer zostaje — sudo -u postgres psql nadal działa)"
sed -i \
  -e '/^host[[:space:]]\+all[[:space:]]\+all[[:space:]]\+127\.0\.0\.1\/32/s/ident$/scram-sha-256/' \
  -e '/^host[[:space:]]\+all[[:space:]]\+all[[:space:]]\+::1\/128/s/ident$/scram-sha-256/' \
  "${PG_HBA}"

echo "==> Reguły logowania (bez replication):"
grep -E '^(local|host)[[:space:]]+all[[:space:]]+all' "${PG_HBA}" || true

echo "==> Restart PostgreSQL"
systemctl restart postgresql
systemctl is-active postgresql

echo "==> Test admin (peer): sudo -u postgres psql"
if sudo -u postgres psql -tAc "SELECT 1" | grep -q 1; then
  echo "Admin postgres: OK"
else
  echo "BŁĄD: admin postgres nie łączy się"
  exit 1
fi

echo "==> Użytkownik i baza (${POSTGRES_USER} / ${POSTGRES_DB})"
sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DO \$do\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${PG_USER}') THEN
    EXECUTE format('CREATE USER %I WITH PASSWORD %L', '${PG_USER}', '${PG_PASS}');
  END IF;
END
\$do\$;

SELECT format('CREATE DATABASE %I OWNER %I', '${PG_DB}', '${PG_USER}')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${PG_DB}')\gexec

SELECT format('GRANT ALL PRIVILEGES ON DATABASE %I TO %I', '${PG_DB}', '${PG_USER}')\gexec
SELECT format('ALTER USER %I CREATEDB', '${PG_USER}')\gexec
SQL

echo ""
echo "==> Wymagane rozszerzenie PostgreSQL (ExclusionConstraint / kalendarz)"
if ! sudo -u postgres psql -d "${POSTGRES_DB}" -tAc \
  "SELECT 1 FROM pg_available_extensions WHERE name = 'btree_gist'" | grep -q 1; then
  echo "Zainstaluj pakiet contrib (Fedora, PostgreSQL 18):"
  echo "  sudo dnf install -y postgresql18-contrib"
  echo "  sudo systemctl restart postgresql"
else
  sudo -u postgres psql -d "${POSTGRES_DB}" -c "CREATE EXTENSION IF NOT EXISTS btree_gist;"
  echo "btree_gist: OK"
fi

echo ""
echo "Gotowe. W pgAdmin użyj danych z pliku .env:"
echo "  Host: ${POSTGRES_HOST} | Port: ${POSTGRES_PORT}"
echo "  Database: ${POSTGRES_DB} | User: ${POSTGRES_USER}"
