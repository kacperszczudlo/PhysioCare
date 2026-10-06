from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import EmailValidator

EMAIL_REQUIRED: str = 'Podaj adres e-mail.'
EMAIL_INVALID: str = 'Podaj prawidłowy adres e-mail (np. jan.kowalski@example.com).'
EMAIL_TAKEN: str = (
    'Ten adres e-mail jest już zarejestrowany. Zaloguj się lub użyj innego adresu.'
)
EMAIL_TAKEN_GOOGLE: str = (
    'Ten adres e-mail jest już zarejestrowany w PhysioCare. '
    'Zamiast rejestracji użyj logowania (Google lub hasło).'
)
EMAIL_TOO_LONG: str = 'Adres e-mail może mieć co najwyżej 254 znaki.'

EMAIL_FIELD_ERRORS: dict[str, str] = {
    'blank': EMAIL_REQUIRED,
    'required': EMAIL_REQUIRED,
    'null': EMAIL_REQUIRED,
    'invalid': EMAIL_INVALID,
    'max_length': EMAIL_TOO_LONG,
}

_email_validator: EmailValidator = EmailValidator(message=EMAIL_INVALID)


def normalize_and_validate_email(value: str | None) -> str:
    """Normalizuje oraz waliduje poprawność formatu adresu e-mail.

    Args:
        value (str | None): Weryfikowany adres e-mail.

    Returns:
        str: Znormalizowany ciąg adresu e-mail (usunięte białe znaki).

    Raises:
        DjangoValidationError: Gdy adres e-mail jest pusty, przekracza 254 znaki, ma zły typ lub nieprawidłowy format.
    """
    if value is not None and not isinstance(value, str):
        raise DjangoValidationError(EMAIL_INVALID, code='invalid')

    if value is None or value.strip() == '':
        raise DjangoValidationError(EMAIL_REQUIRED, code='required')

    email = value.strip()
    if len(email) > 254:
        raise DjangoValidationError(EMAIL_TOO_LONG, code='max_length')

    try:
        _email_validator(email)
    except DjangoValidationError as exc:
        raise DjangoValidationError(EMAIL_INVALID, code='invalid') from exc

    return email.lower()
