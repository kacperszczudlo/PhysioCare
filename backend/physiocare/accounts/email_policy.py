"""Email validation with Polish user-facing messages."""

from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import EmailValidator

EMAIL_REQUIRED = 'Podaj adres e-mail.'
EMAIL_INVALID = 'Podaj prawidłowy adres e-mail (np. jan.kowalski@example.com).'
EMAIL_TAKEN = (
    'Ten adres e-mail jest już zarejestrowany. Zaloguj się lub użyj innego adresu.'
)
EMAIL_TAKEN_GOOGLE = (
    'Ten adres e-mail jest już zarejestrowany w PhysioCare. '
    'Zamiast rejestracji użyj logowania (Google lub hasło).'
)
EMAIL_TOO_LONG = 'Adres e-mail może mieć co najwyżej 254 znaki.'

EMAIL_FIELD_ERRORS = {
    'blank': EMAIL_REQUIRED,
    'required': EMAIL_REQUIRED,
    'null': EMAIL_REQUIRED,
    'invalid': EMAIL_INVALID,
    'max_length': EMAIL_TOO_LONG,
}

_email_validator = EmailValidator(message=EMAIL_INVALID)


def normalize_and_validate_email(value: str | None) -> str:
    """Normalize and validate email format. Raises DjangoValidationError with PL message."""
    if value is None or str(value).strip() == '':
        raise DjangoValidationError(EMAIL_REQUIRED, code='required')

    email = str(value).strip()
    if len(email) > 254:
        raise DjangoValidationError(EMAIL_TOO_LONG, code='max_length')

    try:
        _email_validator(email)
    except DjangoValidationError as exc:
        raise DjangoValidationError(EMAIL_INVALID, code='invalid') from exc

    return email
