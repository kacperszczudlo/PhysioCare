#!/usr/bin/env bash
# Opcjonalnie: nadaje CREATEDB (gdy chcesz osobną bazę test_physiocare)
# Uruchom: sudo bash scripts/grant-test-db-privileges.sh
# Testy działają też BEZ tego — używają bazy z POSTGRES_DB w .env

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Brak pliku ${ENV_FILE}."
  echo "Skopiuj: cp .env.example .env i uzupełnij POSTGRES_USER."
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

: "${POSTGRES_USER:?Ustaw POSTGRES_USER w .env}"

sql_quote() {
  printf '%s' "$1" | sed "s/'/''/g"
}

PG_USER="$(sql_quote "${POSTGRES_USER}")"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Uruchom: sudo bash scripts/grant-test-db-privileges.sh"
  exit 1
fi

sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
SELECT format('ALTER USER %I CREATEDB', '${PG_USER}')\gexec
SQL

echo "${POSTGRES_USER} ma teraz CREATEDB — pytest może utworzyć osobną bazę testową."
