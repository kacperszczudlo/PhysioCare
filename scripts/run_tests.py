#!/usr/bin/env python3
"""Uruchamia pytest z coverage i raportem HTML."""
from __future__ import annotations

import sys

from _common import ROOT_DIR, backend_python, run


def main() -> int:
    backend = ROOT_DIR / "backend"
    python = backend_python()
    requirements = backend / "requirements.txt"

    print("==> pip install -r requirements.txt")
    run([str(python), "-m", "pip", "install", "-q", "-r", str(requirements)])

    reports = backend / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    print("==> pytest")
    completed = run(
        [
            str(python),
            "-m",
            "pytest",
            "tests",
            "--cov=physiocare",
            "--cov-config=.coveragerc",
            "--cov-report=term-missing",
            "--cov-report=html:reports/coverage",
            "--html=reports/pytest-report.html",
            "--self-contained-html",
        ],
        cwd=backend,
        check=False,
    )

    print()
    print(f"Raport HTML: {backend / 'reports' / 'pytest-report.html'}")
    print(f"Coverage HTML: {backend / 'reports' / 'coverage' / 'index.html'}")
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
