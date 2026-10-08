"""Narzędzie CLI i generator SQL do tworzenia lub awansu konta administratora w PhysioCare."""

from __future__ import annotations

import getpass
import logging
import os
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from accounts.models import RoleChoices
from accounts.password_policy import enforce_password_policy

logger = logging.getLogger('physiocare.auth')
User = get_user_model()


def generate_sql_queries(
    email: str, password: str, first_name: str, last_name: str
) -> str:
    """Generuje gotowe zapytania SQL INSERT i UPDATE z hashem Django PBKDF2.

    Args:
        email (str): Adres e-mail administratora.
        password (str): Hasło w postaci jawnej do zahashowania.
        first_name (str): Imię administratora.
        last_name (str): Nazwisko administratora.

    Returns:
        str: Sformatowany skrypt SQL do wykonania w konsoli PostgreSQL.
    """
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


class Command(BaseCommand):
    """Zarządza kontem Administratora PhysioCare (tworzenie, awans, generowanie SQL)."""

    help = 'Tworzy nowe konto administratora, awansuje istniejącego użytkownika lub generuje zapytania SQL.'

    def add_arguments(self, parser: Any) -> None:
        """Konfiguruje flagi i parametry wiersza poleceń dla komendy zarządzania.

        Args:
            parser (Any): Parser argumentów CLI Django.
        """
        parser.add_argument('--email', '-e', type=str, help='Adres e-mail administratora')
        parser.add_argument(
            '--password',
            '-p',
            type=str,
            help='Hasło administratora (dla skryptów CI/CD zalecana zmienna env DJANGO_SUPERUSER_PASSWORD)',
        )
        parser.add_argument('--first-name', default='Admin', help='Imię (domyślnie: Admin)')
        parser.add_argument('--last-name', default='System', help='Nazwisko (domyślnie: System)')
        parser.add_argument(
            '--promote',
            action='store_true',
            help='Awansuj istniejącego użytkownika na rolę ADMIN (oraz flagi is_staff, is_superuser)',
        )
        parser.add_argument(
            '--generate-sql',
            action='store_true',
            help='Wygeneruj i wyświetl kod SQL z zahashowanym hasłem bez łączenia z bazą',
        )
        parser.add_argument(
            '--noinput',
            action='store_true',
            help='Wyłącza pytania interaktywne w terminalu',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Główny punkt wejścia wykonania komendy tworzenia lub awansu administratora.

        Args:
            *args (Any): Pozycyjne argumenty wywołania.
            **options (Any): Słownik opcji wiersza poleceń (flagi).

        Raises:
            CommandError: W przypadku błędnych danych wejściowych lub niespełnienia polityki hasła.
        """
        email = (options.get('email') or '').strip().lower()
        password = options.get('password')
        first_name = options.get('first_name', 'Admin').strip()
        last_name = options.get('last_name', 'System').strip()
        promote = options.get('promote', False)
        generate_sql = options.get('generate_sql', False)
        noinput = options.get('noinput', False)

        # 1. Pobranie adresu e-mail jeśli brak
        if not email:
            if noinput:
                raise CommandError('Adres e-mail jest wymagany w trybie --noinput.')
            email = input('Podaj adres e-mail administratora: ').strip().lower()

        if not email or '@' not in email:
            raise CommandError('Podaj prawidłowy adres e-mail.')

        # 2. Pobranie hasła jeśli brak (ze zmiennej środowiskowej lub promptu)
        if not password:
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD') or os.environ.get('ADMIN_PASSWORD')

        if not password and not promote and not generate_sql:
            if noinput:
                raise CommandError('Hasło jest wymagane w trybie --noinput (użyj --password lub zmiennej DJANGO_SUPERUSER_PASSWORD).')
            password = self._prompt_password('Podaj hasło administratora: ')

        # 3. Tryb generowania SQL
        if generate_sql:
            if not password:
                if noinput:
                    raise CommandError('Hasło jest wymagane do wygenerowania hasha w SQL.')
                password = self._prompt_password('Podaj hasło do wygenerowania hasha w SQL: ', confirm=False)
            self._validate_password_safely(password)
            sql = generate_sql_queries(email, password, first_name, last_name)
            self.stdout.write(sql)
            return

        # 4. Tryb awansu istniejącego użytkownika
        if promote:
            user = User.objects.filter(email__iexact=email).first()
            if not user:
                raise CommandError(f"Użytkownik o adresie '{email}' nie istnieje.")

            user.role = RoleChoices.ADMIN
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            if not user.email_verified_at:
                user.email_verified_at = timezone.now()

            if password:
                self._validate_password_safely(password, user=user)
                user.set_password(password)

            user.save()
            logger.info('Użytkownik %s został awansowany na rolę ADMINISTRATORA (ADMIN).', email)
            self.stdout.write(
                self.style.SUCCESS(
                    f"SUKCES: Użytkownik '{email}' został awansowany na rolę ADMINISTRATORA (ADMIN)."
                )
            )
            return

        # 5. Tworzenie lub aktualizacja administratora
        existing_user = User.objects.filter(email__iexact=email).first()
        if existing_user:
            self.stdout.write(
                self.style.WARNING(
                    f"UWAGA: Użytkownik o adresie '{email}' już istnieje (rola: {existing_user.role})."
                )
            )
            if noinput:
                raise CommandError(f"Użytkownik o adresie '{email}' już istnieje. Użyj --promote aby zaktualizować rolę.")

            choice = input('Czy chcesz awansować go na Administratora i zaktualizować uprawnienia? [t/N]: ').strip().lower()
            if choice not in ('t', 'tak', 'y', 'yes'):
                self.stdout.write('Operacja anulowana.')
                return

            existing_user.role = RoleChoices.ADMIN
            existing_user.is_staff = True
            existing_user.is_superuser = True
            existing_user.is_active = True
            if not existing_user.email_verified_at:
                existing_user.email_verified_at = timezone.now()

            if password:
                self._validate_password_safely(password, user=existing_user)
                existing_user.set_password(password)

            existing_user.save()
            logger.info('Użytkownik %s został zaktualizowany na rolę Administratora.', email)
            self.stdout.write(
                self.style.SUCCESS(
                    f"SUKCES: Użytkownik '{email}' został zaktualizowany i posiada uprawnienia Administratora."
                )
            )
            return

        # Utworzenie nowego superusera
        self._validate_password_safely(password)
        new_admin = User.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=RoleChoices.ADMIN,
        )
        logger.info('Utworzono nowego administratora %s (ID: %s).', new_admin.email, new_admin.id)
        self.stdout.write(
            self.style.SUCCESS(
                f"SUKCES: Utworzono nowego Administratora '{new_admin.email}' (ID: {new_admin.id})."
            )
        )

    def _prompt_password(self, prompt_text: str, confirm: bool = True) -> str:
        """Pobiera hasło z terminala z opcjonalnym potwierdzeniem.

        Args:
            prompt_text (str): Komunikat wyświetlany użytkownikowi w terminalu.
            confirm (bool, optional): Czy wymagać ponownego wpisania hasła do potwierdzenia. Domyślnie True.

        Returns:
            str: Wprowadzone hasło w postaci jawnej.
        """
        while True:
            pwd = getpass.getpass(prompt_text)
            if not pwd:
                self.stdout.write(self.style.ERROR('Hasło nie może być puste.'))
                continue
            if confirm:
                confirm_pwd = getpass.getpass('Potwierdź hasło: ')
                if pwd != confirm_pwd:
                    self.stdout.write(self.style.ERROR('BŁĄD: Hasła nie są identyczne. Spróbuj ponownie.'))
                    continue
            return pwd

    def _validate_password_safely(self, password: str, user: Any = None) -> None:
        """Weryfikuje hasło względem polityki bezpieczeństwa projektu.

        Args:
            password (str): Hasło do sprawdzenia.
            user (Any, optional): Obiekt użytkownika powiązany z hasłem. Domyślnie None.

        Raises:
            CommandError: W przypadku naruszenia reguł walidacji bezpieczeństwa hasła.
        """
        try:
            enforce_password_policy(password, user=user)
        except DjangoValidationError as exc:
            msg = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
            raise CommandError(f'Hasło nie spełnia wymogów bezpieczeństwa: {msg}') from exc

