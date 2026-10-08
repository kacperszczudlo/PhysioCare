#!/usr/bin/env python3
"""Narzędzie CLI i generator SQL do tworzenia lub awansu konta administratora w PhysioCare.

Skrypt stanowi kompatybilny wstecznie wrapper wywołujący natywną komendę Django:
  python manage.py create_admin

Użycie:
  # Interaktywne tworzenie konta:
  python scripts/create_admin.py

  # Szybkie utworzenie nowego admina z flagami:
  python scripts/create_admin.py --email admin@physiocare.pl --password "TajneHaslo123!" --first-name "Admin" --last-name "System"

  # Awans istniejącego użytkownika na ADMIN:
  python scripts/create_admin.py --promote --email uzytkownik@physiocare.pl

  # Wygenerowanie czystego zapytania SQL bez dotykania bazy danych:
  python scripts/create_admin.py --generate-sql --email admin@physiocare.pl --password "TajneHaslo123!"
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ustalenie ścieżek do projektu backendowego
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend" / "physiocare"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "physiocare.settings")

import django

django.setup()

from accounts.management.commands.create_admin import generate_sql_queries
from django.core.management import call_command
from django.core.management.base import CommandError


def main() -> int:
    """Uruchamia komendę create_admin z przekazanymi argumentami wiersza poleceń."""
    try:
        call_command("create_admin", *sys.argv[1:])
        return 0
    except CommandError as err:
        print(f"BŁĄD: {err}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nPrzerwano operację przez użytkownika.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
