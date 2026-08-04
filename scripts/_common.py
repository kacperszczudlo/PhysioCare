"""Wspólne helpers dla skryptów PhysioCare (Windows / Linux)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPTS_DIR.parent


def load_dotenv(path: Path | None = None) -> Path:
    env_path = path or (ROOT_DIR / ".env")
    if not env_path.is_file():
        raise SystemExit(
            f"Brak pliku {env_path}. Skopiuj: "
            f"Copy-Item .env.example .env  (Windows) / cp .env.example .env  (Linux)"
        )
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        os.environ[key] = value
    return env_path


def require_env(*names: str) -> None:
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise SystemExit(f"Ustaw w .env: {', '.join(missing)}")


@dataclass(frozen=True)
class PostgresEnv:
    db: str
    user: str
    password: str
    host: str
    port: str


def postgres_env() -> PostgresEnv:
    require_env("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
    return PostgresEnv(
        db=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ.get("POSTGRES_HOST") or "localhost",
        port=os.environ.get("POSTGRES_PORT") or "5432",
    )


def admin_credentials() -> tuple[str, str]:
    user = os.environ.get("POSTGRES_ADMIN_USER") or "postgres"
    password = (
        os.environ.get("POSTGRES_ADMIN_PASSWORD")
        or os.environ.get("POSTGRES_PASSWORD")
        or ""
    )
    if not password:
        password = input(f"Haslo admina PostgreSQL ({user}): ").strip()
    if not password:
        raise SystemExit("Brak hasla admina (POSTGRES_ADMIN_PASSWORD).")
    return user, password


def _pg_bin_name(base: str) -> str:
    if sys.platform.startswith("win"):
        return base if base.lower().endswith(".exe") else f"{base}.exe"
    return base.replace(".exe", "")


def find_postgres_bin(name: str) -> str:
    exe = _pg_bin_name(name)
    found = shutil.which(exe) or shutil.which(name)
    if found:
        return found

    search_roots: list[Path] = []
    if sys.platform.startswith("win"):
        for key in ("ProgramFiles", "ProgramFiles(x86)"):
            root = os.environ.get(key)
            if root:
                search_roots.append(Path(root) / "PostgreSQL")
    else:
        search_roots.extend(
            [
                Path("/usr/lib/postgresql"),
                Path("/usr/pgsql-16"),
                Path("/usr/pgsql-18"),
                Path("/usr/bin"),
            ]
        )

    matches: list[Path] = []
    for root in search_roots:
        if not root.exists():
            continue
        matches.extend(root.rglob(exe))

    if matches:
        matches.sort(key=lambda p: str(p), reverse=True)
        return str(matches[0])

    raise SystemExit(
        f"Nie znaleziono {exe}. Dodaj binaria PostgreSQL do PATH "
        r"(np. C:\Program Files\PostgreSQL\18\bin)."
    )


def backend_python() -> Path:
    backend = ROOT_DIR / "backend"
    candidates = [
        backend / "venv" / "Scripts" / "python.exe",
        backend / "venv" / "bin" / "python",
        backend / ".venv" / "Scripts" / "python.exe",
        backend / ".venv" / "bin" / "python",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise SystemExit(
        "Brak venv. Utworz:\n"
        "  cd backend\n"
        "  python -m venv venv\n"
        "  # Windows: .\\venv\\Scripts\\Activate.ps1\n"
        "  # Linux:   source venv/bin/activate\n"
        "  pip install -r requirements.txt"
    )


def run(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        env=merged,
        check=check,
        text=True,
    )


def sql_literal(value: str) -> str:
    return value.replace("'", "''")
