#!/usr/bin/env python3
"""Opcjonalnie: nadaje CREATEDB uzytkownikowi z .env."""
from __future__ import annotations

from _common import (
    admin_credentials,
    find_postgres_bin,
    load_dotenv,
    require_env,
    run,
)
import os


def main() -> None:
    load_dotenv()
    require_env("POSTGRES_USER")
    pg_user = os.environ["POSTGRES_USER"]
    host = os.environ.get("POSTGRES_HOST") or "localhost"
    port = os.environ.get("POSTGRES_PORT") or "5432"
    admin_user, admin_password = admin_credentials()
    psql = find_postgres_bin("psql")

    sql = f'ALTER USER "{pg_user.replace(chr(34), chr(34)+chr(34))}" CREATEDB;'
    run(
        [
            psql,
            "-h",
            host,
            "-p",
            port,
            "-U",
            admin_user,
            "-d",
            "postgres",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            sql,
        ],
        env={"PGPASSWORD": admin_password},
    )
    print(f"{pg_user} ma teraz CREATEDB — pytest moze utworzyc osobna baze testowa.")


if __name__ == "__main__":
    main()
