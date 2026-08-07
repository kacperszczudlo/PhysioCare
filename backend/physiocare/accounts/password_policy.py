"""Password strength policy with Polish user-facing messages."""

from __future__ import annotations

import re

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

MIN_PASSWORD_LENGTH = 8
# Letters, digits, underscore are excluded — everything else counts as special.
SPECIAL_CHAR_PATTERN = re.compile(r'[^A-Za-z0-9_]')

PASSWORD_TOO_SHORT = (
    f'Hasło musi mieć co najmniej {MIN_PASSWORD_LENGTH} znaków.'
)
PASSWORD_TOO_COMMON = 'To hasło jest zbyt popularne. Wybierz bardziej unikalne.'
PASSWORD_ENTIRELY_NUMERIC = 'Hasło nie może składać się wyłącznie z cyfr.'
PASSWORD_TOO_SIMILAR = (
    'Hasło jest zbyt podobne do Twoich danych (e-mail, imię lub nazwisko).'
)
PASSWORD_NO_SPECIAL = (
    'Hasło musi zawierać co najmniej jeden znak specjalny '
    '(np. ! @ # $ % & *).'
)
PASSWORD_REQUIRED = 'Podaj hasło.'

_PASSWORD_ERROR_BY_CODE = {
    'password_too_short': PASSWORD_TOO_SHORT,
    'password_too_common': PASSWORD_TOO_COMMON,
    'password_entirely_numeric': PASSWORD_ENTIRELY_NUMERIC,
    'password_too_similar': PASSWORD_TOO_SIMILAR,
    'password_no_special': PASSWORD_NO_SPECIAL,
}


class SpecialCharacterValidator:
    """Require at least one non-alphanumeric special character."""

    def validate(self, password, user=None):
        if not SPECIAL_CHAR_PATTERN.search(password or ''):
            raise DjangoValidationError(
                PASSWORD_NO_SPECIAL,
                code='password_no_special',
            )

    def get_help_text(self):
        return PASSWORD_NO_SPECIAL


def polish_password_messages(exc: DjangoValidationError) -> list[str]:
    messages: list[str] = []
    for error in exc.error_list:
        code = getattr(error, 'code', None)
        if code in _PASSWORD_ERROR_BY_CODE:
            messages.append(_PASSWORD_ERROR_BY_CODE[code])
        else:
            messages.append(str(error.message))
    return messages or [PASSWORD_TOO_SHORT]


def enforce_password_policy(password: str, user=None) -> str:
    """Validate password against Django AUTH_PASSWORD_VALIDATORS.

    Raises DjangoValidationError with Polish messages.
    """
    if password is None or str(password).strip() == '':
        raise DjangoValidationError(PASSWORD_REQUIRED, code='required')

    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        raise DjangoValidationError(polish_password_messages(exc)) from exc

    return password
