#!/usr/bin/env python3
"""Narzędzie CLI i generator SQL do tworzenia konta administratora w PhysioCare.

Użycie:
  # Interaktywne tworzenie konta:
  python scripts/create_admin.py

  # Szybkie utworzenie nowego admina:
  python scripts/create_admin.py --email admin@physiocare.pl --password "TajneHaslo123!" --first-name "Admin" --last-name "System"

  # Awans istniejącego użytkownika na ADMIN:
  python scripts/create_admin.py --promote --email uzytkownik@physiocare.pl

  # Wygenerowanie czystego zapytania SQL bez dotykania bazy danych:
  python scripts/create_admin.py --generate-sql --email admin@physiocare.pl --password "TajneHaslo123!"
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

# Ustalenie ścieżek
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend" / "physiocare"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "physiocare.settings")

import django

django.setup()

from accounts.models import CustomUser, RoleChoices
from django.contrib.auth.hashers import make_password
from django.utils import timezone


def generate_sql_queries(
    email: str, password: str, first_name: str, last_name: str
) -> str:
    """Generuje gotowe zapytania SQL INSERT i UPDATE."""
    hashed_pwd = make_password(password)
    sql_escaped_email = email.replace("'", "''")
    sql_escaped_hash = hashed_pwd.replace("'", "''")
    sql_escaped_first = first_name.replace("'", "''")
    sql_escaped_last = last_name.replace("'", "''")

    return f"""-- ==============================================================================
-- PHYSIOCARE: ZAPYTANIA SQL DLA ADMINISTRATORA
-- ==============================================================================

-- OPCJA 1: Utworzenie NOWEGO konta Administratora (INSERT)
-- Wygenerowany poprawny hash Django PBKDF2 (SHA-256) dla podanego hasła:
INSERT INTO users (
    id,
    email,
    password,
    role,
    first_name,
    last_name,
    is_staff,
    is_superuser,
    is_active,
    email_verified_at,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    LOWER('{sql_escaped_email}'),
    '{sql_escaped_hash}',
    'ADMIN',
    '{sql_escaped_first}',
    '{sql_escaped_last}',
    TRUE,
    TRUE,
    TRUE,
    NOW(),
    NOW(),
    NOW()
)
ON CONFLICT (LOWER(email)) DO UPDATE SET
    role = 'ADMIN',
    is_staff = TRUE,
    is_superuser = TRUE,
    is_active = TRUE,
    password = EXCLUDED.password,
    email_verified_at = COALESCE(users.email_verified_at, NOW()),
    updated_at = NOW();

-- ------------------------------------------------------------------------------

-- OPCJA 2: Awans ISTNIEJĄCEGO konta na Administratora (UPDATE)
-- (Przydatne, gdy konto zostało zarejestrowane wcześniej przez aplikację web/mobile)
UPDATE users
SET
    role = 'ADMIN',
    is_staff = TRUE,
    is_superuser = TRUE,
    is_active = TRUE,
    email_verified_at = COALESCE(email_verified_at, NOW()),
    updated_at = NOW()
WHERE LOWER(email) = LOWER('{sql_escaped_email}');
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Zarządzanie kontem Administratora PhysioCare"
    )
    parser.add_argument("--email", "-e", help="Adres e-mail administratora")
    parser.add_argument("--password", "-p", help="Hasło administratora")
    parser.add_argument("--first-name", default="Admin", help="Imię (domyślnie: Admin)")
    parser.add_argument(
        "--last-name", default="System", help="Nazwisko (domyślnie: System)"
    )
    parser.add_argument(
        "--promote",
        action="store_true",
        help="Awansuj istniejącego użytkownika na rolę ADMIN",
    )
    parser.add_argument(
        "--generate-sql",
        action="store_true",
        help="Wygeneruj i wyświetl kod SQL z zahashowanym hasłem",
    )

    args = parser.parse_args()

    email = (args.email or "").strip().lower()
    if not email:
        email = input("Podaj adres e-mail administratora: ").strip().lower()

    if not email:
        print("BŁĄD: Adres e-mail jest wymagany.", file=sys.stderr)
        return 1

    password = args.password
    if not password and not args.promote and not args.generate_sql:
        password = getpass.getpass("Podaj hasło administratora: ")
        confirm_pwd = getpass.getpass("Potwierdź hasło: ")
        if password != confirm_pwd:
            print("BŁĄD: Hasła nie są identyczne.", file=sys.stderr)
            return 1

    if args.generate_sql:
        if not password:
            password = getpass.getpass("Podaj hasło do wygenerowania hasha w SQL: ")
        print(generate_sql_queries(email, password, args.first_name, args.last_name))
        return 0

    if args.promote:
        try:
            user = CustomUser.objects.get(email__iexact=email)
        except CustomUser.DoesNotExist:
            print(
                f"BŁĄD: Użytkownik o adresie '{email}' nie istnieje.", file=sys.stderr
            )
            return 1

        user.role = RoleChoices.ADMIN
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        if not user.email_verified_at:
            user.email_verified_at = timezone.now()
        if password:
            user.set_password(password)
        user.save()
        print(
            f"SUKCES: Użytkownik '{email}' został awansowany na rolę ADMINISTRATORA (ADMIN)."
        )
        return 0

    # Tworzenie nowego superużytkownika / administratora
    if not password:
        password = getpass.getpass("Podaj hasło administratora: ")

    existing_user = CustomUser.objects.filter(email__iexact=email).first()
    if existing_user:
        print(
            f"UWAGA: Użytkownik o adresie '{email}' już istnieje (rola: {existing_user.role})."
        )
        choice = (
            input("Czy chcesz awansować go na Administratora i zmienić hasło? [t/N]: ")
            .strip()
            .lower()
        )
        if choice in ("t", "tak", "y", "yes"):
            existing_user.role = RoleChoices.ADMIN
            existing_user.is_staff = True
            existing_user.is_superuser = True
            existing_user.is_active = True
            if not existing_user.email_verified_at:
                existing_user.email_verified_at = timezone.now()
            existing_user.set_password(password)
            existing_user.save()
            print(
                f"SUKCES: Użytkownik '{email}' został zaktualizowany i ma teraz uprawnienia Administratora."
            )
            return 0
        print("Anulowano.")
        return 1

    user = CustomUser.objects.create_superuser(
        email=email,
        password=password,
        first_name=args.first_name,
        last_name=args.last_name,
        role=RoleChoices.ADMIN,
    )
    print(f"SUKCES: Utworzono nowego Administratora '{user.email}' (ID: {user.id}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
