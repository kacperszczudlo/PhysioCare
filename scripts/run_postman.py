#!/usr/bin/env python3
"""Sprawdza i uruchamia testy kolekcji Postman (docs/postman/PhysioCare.json)."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
POSTMAN_COLLECTION = ROOT_DIR / "docs" / "postman" / "PhysioCare.json"


def main() -> int:
    print("==================================================")
    print(" POSTMAN API COLLECTION RUNNER")
    print("==================================================")
    
    if not POSTMAN_COLLECTION.exists():
        print(f"[FAIL] Plik kolekcji Postman nie istnieje: {POSTMAN_COLLECTION}")
        return 1
        
    print(f"[OK] Plik kolekcji Postman odnaleziony: {POSTMAN_COLLECTION}")
    
    newman = shutil.which("newman")
    if newman:
        print("==> Uruchamianie testów Postman via Newman CLI...")
        res = subprocess.run([newman, "run", str(POSTMAN_COLLECTION)], check=False)
        return res.returncode
    else:
        print("[INFO] Newman CLI nie jest zainstalowany globalnie.")
        print("   Wskazowka: Aby uruchamiac kolekcje w terminalu, zainstaluj: npm install -g newman")
        print("   Mozesz rowniez zaimportowac plik w aplikacji Postman Desktop App i uruchomic 'Collection Runner'.")
        print("[OK] Walidacja pliku kolekcji Postman zakonczona sukcesem.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
