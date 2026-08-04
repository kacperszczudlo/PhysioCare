#!/usr/bin/env python3
"""Pierwsza konfiguracja PostgreSQL: user, baza, btree_gist."""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from _common import (
    ROOT_DIR,
    admin_credentials,
    find_postgres_bin,
    load_dotenv,
    postgres_env,
    run,
    sql_literal,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-pg-hba",
        action="store_true",
        help="Nie ruszaj pg_hba.conf (domyslne zachowanie bezpieczne).",
    )
    args = parser.parse_args()

    load_dotenv()
    pg = postgres_env()
    admin_user, admin_password = admin_credentials()
    psql = find_postgres_bin("psql")
    print(f"==> psql: {psql}")

    if not args.skip_pg_hba:
        print("==> pg_hba: pomijam automatyczna edycje (uzyj -- bez zmian; EDB zwykle ma scram).")

    env = {"PGPASSWORD": admin_password}
    print(f"==> Test polaczenia admin ({admin_user} @ {pg.host}:{pg.port})")
    run(
        [psql, "-h", pg.host, "-p", pg.port, "-U", admin_user, "-d", "postgres",
         "-v", "ON_ERROR_STOP=1", "-tAc", "SELECT 1"],
        env=env,
    )
    print("Admin: OK")

    user_lit = sql_literal(pg.user)
    pass_lit = sql_literal(pg.password)
    db_lit = sql_literal(pg.db)
    setup_sql = f"""
DO $do$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{user_lit}') THEN
    EXECUTE format('CREATE USER %I WITH PASSWORD %L', '{user_lit}', '{pass_lit}');
  ELSE
    EXECUTE format('ALTER USER %I WITH PASSWORD %L', '{user_lit}', '{pass_lit}');
  END IF;
END
$do$;

SELECT format('CREATE DATABASE %I OWNER %I', '{db_lit}', '{user_lit}')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '{db_lit}')\\gexec

SELECT format('GRANT ALL PRIVILEGES ON DATABASE %I TO %I', '{db_lit}', '{user_lit}')\\gexec
SELECT format('ALTER USER %I CREATEDB', '{user_lit}')\\gexec
"""
    print(f"==> Uzytkownik i baza ({pg.user} / {pg.db})")
    with tempfile.NamedTemporaryFile(
        "w", suffix=".sql", delete=False, encoding="utf-8", newline="\n"
    ) as tmp:
        tmp.write(setup_sql)
        tmp_path = Path(tmp.name)
    try:
        run(
            [psql, "-h", pg.host, "-p", pg.port, "-U", admin_user, "-d", "postgres",
             "-v", "ON_ERROR_STOP=1", "-f", str(tmp_path)],
            env=env,
        )
    finally:
        tmp_path.unlink(missing_ok=True)

    print("==> Rozszerzenie btree_gist")
    try:
        run(
            [psql, "-h", pg.host, "-p", pg.port, "-U", admin_user, "-d", pg.db,
             "-v", "ON_ERROR_STOP=1", "-c", "CREATE EXTENSION IF NOT EXISTS btree_gist;"],
            env=env,
        )
        print("btree_gist: OK")
    except Exception:
        print(
            "UWAGA: btree_gist nie utworzone. Zainstaluj postgresql-contrib / Stack Builder."
        )
        raise

    print()
    print("Gotowe. W pgAdmin uzyj danych z .env:")
    print(f"  Host: {pg.host} | Port: {pg.port}")
    print(f"  Database: {pg.db} | User: {pg.user}")
    print(f"Repo root: {ROOT_DIR}")


if __name__ == "__main__":
    main()
