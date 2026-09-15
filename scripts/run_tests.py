#!/usr/bin/env python3
"""Uruchamia pełną paczkę testów PhysioCare: Backend (pytest), Web (vitest) oraz Mobile (vitest)."""
from __future__ import annotations

import subprocess
import sys

from _common import ROOT_DIR, backend_python, run


def main() -> int:
    backend = ROOT_DIR / "backend"
    web = ROOT_DIR / "web"
    mobile = ROOT_DIR / "mobile"
    python = backend_python()
    requirements = backend / "requirements.txt"

    print("==================================================")
    print(" 1. BACKEND TESTS (pytest)")
    print("==================================================")
    print("==> pip install -r requirements.txt")
    run([str(python), "-m", "pip", "install", "-q", "-r", str(requirements)])

    reports = backend / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    print("==> pytest")
    backend_res = run(
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

    print("\n==================================================")
    print(" 2. WEB APP TESTS (Vitest)")
    print("==================================================")
    web_res = subprocess.run(["cmd", "/c", "npm", "test"], cwd=web, check=False)

    print("\n==================================================")
    print(" 3. MOBILE APP TESTS (Vitest)")
    print("==================================================")
    mobile_res = subprocess.run(["cmd", "/c", "npm", "test"], cwd=mobile, check=False)

    print("\n==================================================")
    print(" PODSUMOWANIE PAKIETU TESTÓW PHYSIOCARE")
    print("==================================================")
    print(f"Backend Pytest exit code: {backend_res.returncode}")
    print(f"Web Vitest exit code:     {web_res.returncode}")
    print(f"Mobile Vitest exit code:  {mobile_res.returncode}")
    print("--------------------------------------------------")

    if backend_res.returncode == 0 and web_res.returncode == 0 and mobile_res.returncode == 0:
        print("[OK] WSZYSTKIE TESTY (BACKEND + WEB + MOBILE) ZAKONCZONE SUKCESEM!")
        return 0
    else:
        print("[FAIL] NIEKTORE TESTY OBLALY!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
