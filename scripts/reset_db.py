#!/usr/bin/env python3
"""Reset bazy dev + swieze migracje Django."""
from __future__ import annotations

from _common import (
    ROOT_DIR,
    backend_python,
    find_postgres_bin,
    load_dotenv,
    postgres_env,
    run,
)


def main() -> None:
    load_dotenv()
    pg = postgres_env()
    dropdb = find_postgres_bin("dropdb")
    createdb = find_postgres_bin("createdb")
    psql = find_postgres_bin("psql")
    python = backend_python()
    env = {"PGPASSWORD": pg.password}

    print(f"Dropping database {pg.db}...")
    run(
        [dropdb, "--if-exists", "-h", pg.host, "-p", pg.port, "-U", pg.user, pg.db],
        env=env,
        check=False,
    )

    print(f"Creating database {pg.db}...")
    try:
        run(
            [createdb, "-h", pg.host, "-p", pg.port, "-U", pg.user, pg.db],
            env=env,
        )
    except Exception as exc:
        raise SystemExit(
            "Nie udalo sie utworzyc bazy. Najpierw: "
            "python scripts/setup_postgres_auth.py"
        ) from exc

    print("Ensuring btree_gist extension...")
    run(
        [
            psql,
            "-h",
            pg.host,
            "-p",
            pg.port,
            "-U",
            pg.user,
            "-d",
            pg.db,
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            "CREATE EXTENSION IF NOT EXISTS btree_gist;",
        ],
        env=env,
    )

    print("Running migrations...")
    run(
        [str(python), "manage.py", "migrate", "--noinput"],
        cwd=ROOT_DIR / "backend" / "physiocare",
    )
    print("Done.")


if __name__ == "__main__":
    main()
