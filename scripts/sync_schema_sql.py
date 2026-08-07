#!/usr/bin/env python3
"""Regeneruje database/schema.sql z biezacej bazy PostgreSQL."""
from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from _common import ROOT_DIR, find_postgres_bin, load_dotenv, postgres_env, run


def main() -> None:
    load_dotenv()
    pg = postgres_env()
    pg_dump = find_postgres_bin("pg_dump")
    env = {"PGPASSWORD": pg.password}
    output = ROOT_DIR / "database" / "schema.sql"

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        run(
            [
                pg_dump,
                "--schema-only",
                "--no-owner",
                "--no-privileges",
                "-h",
                pg.host,
                "-p",
                pg.port,
                "-U",
                pg.user,
                "-f",
                str(tmp_path),
                pg.db,
            ],
            env=env,
        )
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        header = (
            "-- PhysioCare - auto-generated from Django migrations\n"
            f"-- Generated: {stamp}\n"
            "-- Do not edit manually. Run: python scripts/sync_schema_sql.py\n"
            "\n"
        )
        body = tmp_path.read_text(encoding="utf-8")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(header + body, encoding="utf-8", newline="\n")
        print(f"Wrote {output}")
    finally:
        tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
