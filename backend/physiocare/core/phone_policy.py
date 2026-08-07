"""Polish phone number validation with user-facing messages."""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError as DjangoValidationError

PHONE_REQUIRED = 'Podaj numer telefonu.'
PHONE_INVALID = (
    'Podaj prawidłowy polski numer telefonu '
    '(9 cyfr, opcjonalnie z numerem kierunkowym +48).'
)
PHONE_TOO_LONG = 'Numer telefonu może mieć co najwyżej 20 znaków.'

PHONE_FIELD_ERRORS = {
    'blank': PHONE_REQUIRED,
    'required': PHONE_REQUIRED,
    'null': PHONE_REQUIRED,
    'max_length': PHONE_TOO_LONG,
    'invalid': PHONE_INVALID,
}

_NON_DIGIT = re.compile(r'\D+')


def normalize_and_validate_phone(value: str | None, *, allow_blank: bool = True) -> str:
    """Normalize Polish phone to +48XXXXXXXXX. Blank allowed when allow_blank=True."""
    if value is None:
        if allow_blank:
            return ''
        raise DjangoValidationError(PHONE_REQUIRED, code='required')

    raw = str(value).strip()
    if raw == '':
        if allow_blank:
            return ''
        raise DjangoValidationError(PHONE_REQUIRED, code='required')

    if len(raw) > 20:
        raise DjangoValidationError(PHONE_TOO_LONG, code='max_length')

    digits = _NON_DIGIT.sub('', raw)
    if digits.startswith('0048'):
        digits = digits[4:]
    elif digits.startswith('48') and len(digits) == 11:
        digits = digits[2:]
    elif digits.startswith('0') and len(digits) == 10:
        digits = digits[1:]

    if len(digits) != 9 or not digits.isdigit() or digits[0] == '0':
        raise DjangoValidationError(PHONE_INVALID, code='invalid')

    return f'+48{digits}'
