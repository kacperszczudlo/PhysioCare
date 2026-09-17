from __future__ import annotations

import re

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

MIN_PASSWORD_LENGTH: int = 8
SPECIAL_CHAR_PATTERN: re.Pattern[str] = re.compile(r'[^A-Za-z0-9_]')

PASSWORD_TOO_SHORT: str = (
    f'Hasło musi mieć co najmniej {MIN_PASSWORD_LENGTH} znaków.'
)
PASSWORD_TOO_COMMON: str = 'To hasło jest zbyt popularne. Wybierz bardziej unikalne.'
PASSWORD_ENTIRELY_NUMERIC: str = 'Hasło nie może składać się wyłącznie z cyfr.'
PASSWORD_TOO_SIMILAR: str = (
    'Hasło jest zbyt podobne do Twoich danych (e-mail, imię lub nazwisko).'
)
PASSWORD_NO_SPECIAL: str = (
    'Hasło musi zawierać co najmniej jeden znak specjalny '
    '(np. ! @ # $ % & *).'
)
PASSWORD_REQUIRED: str = 'Podaj hasło.'

_PASSWORD_ERROR_BY_CODE: dict[str, str] = {
    'password_too_short': PASSWORD_TOO_SHORT,
    'password_too_common': PASSWORD_TOO_COMMON,
    'password_entirely_numeric': PASSWORD_ENTIRELY_NUMERIC,
    'password_too_similar': PASSWORD_TOO_SIMILAR,
    'password_no_special': PASSWORD_NO_SPECIAL,
}


class SpecialCharacterValidator:
    """Wymaga co najmniej jednego znaku specjalnego (niealfanumerycznego) w haśle."""

    def validate(self, password: str, user: object | None = None) -> None:
        """Waliduje obecność znaku specjalnego w haśle.

        Args:
            password (str): Testowane hasło.
            user (object | None): Opcjonalny obiekt użytkownika.

        Raises:
            DjangoValidationError: Gdy hasło nie zawiera znaku specjalnego lub jest niepoprawnego typu.
        """
        if not isinstance(password, str):
            raise DjangoValidationError(
                PASSWORD_NO_SPECIAL,
                code='password_no_special',
            )

        if not SPECIAL_CHAR_PATTERN.search(password):
            raise DjangoValidationError(
                PASSWORD_NO_SPECIAL,
                code='password_no_special',
            )

    def get_help_text(self) -> str:
        """Zwraca tekst pomocy opisujący wymóg znaku specjalnego.

        Returns:
            str: Tekst pomocy z opisem wymogów.
        """
        return PASSWORD_NO_SPECIAL


def polish_password_messages(exc: DjangoValidationError) -> list[str]:
    """Konwertuje kody błędów walidacji hasła Django na polskie komunikaty.

    Args:
        exc (DjangoValidationError): Wyjątek walidacji Django.

    Returns:
        list[str]: Lista czytelnych polskich komunikatów błędów.

    Raises:
        TypeError: Gdy exc nie jest instancją DjangoValidationError.
    """
    if not isinstance(exc, DjangoValidationError):
        raise TypeError("Argument 'exc' musi być instancją DjangoValidationError.")

    messages: list[str] = []
    for error in exc.error_list:
        code = error.code if hasattr(error, 'code') else None
        if code in _PASSWORD_ERROR_BY_CODE:
            messages.append(_PASSWORD_ERROR_BY_CODE[code])
        else:
            messages.append(str(error.message))
    return messages or [PASSWORD_TOO_SHORT]


def enforce_password_policy(password: str, user: object | None = None) -> str:
    """Weryfikuje zgodność hasła z konfigurowalnymi walidatorami Django.

    Args:
        password (str): Hasło użytkownika.
        user (object | None): Opcjonalny obiekt użytkownika.

    Returns:
        str: Zweryfikowane hasło.

    Raises:
        DjangoValidationError: Gdy hasło jest puste, nie jest tekstem lub nie spełnia wymogów bezpieczeństwa.
    """
    if not isinstance(password, str):
        raise DjangoValidationError(PASSWORD_REQUIRED, code='required')

    if password.strip() == '':
        raise DjangoValidationError(PASSWORD_REQUIRED, code='required')

    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        raise DjangoValidationError(polish_password_messages(exc)) from exc

    return password
