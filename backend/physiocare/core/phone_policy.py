"""International phone validation (E.164) with user-facing messages."""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError as DjangoValidationError

PHONE_REQUIRED = 'Podaj numer telefonu.'
PHONE_INVALID = 'Podaj prawidłowy numer telefonu w formacie międzynarodowym (np. +48123456789).'
PHONE_TOO_LONG = 'Numer telefonu może mieć co najwyżej 20 znaków.'

PHONE_FIELD_ERRORS = {
    'blank': PHONE_REQUIRED,
    'required': PHONE_REQUIRED,
    'null': PHONE_REQUIRED,
    'max_length': PHONE_TOO_LONG,
    'invalid': PHONE_INVALID,
}

_NON_DIGIT = re.compile(r'\D+')
_E164 = re.compile(r'^\+[1-9]\d{7,14}$')


def normalize_and_validate_phone(value: str | None, *, allow_blank: bool = True) -> str:
    """Normalize phone to E.164 (+XXXXXXXX...). Blank allowed when allow_blank=True."""
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
    if not digits:
        raise DjangoValidationError(PHONE_INVALID, code='invalid')

    if digits.startswith('00'):
        digits = digits[2:]
    elif digits.startswith('0') and len(digits) == 10:
        # Legacy Polish trunk prefix: 0XXXXXXXXX
        digits = digits[1:]

    # Bare 9-digit Polish mobile/landline without country code.
    if not raw.startswith('+') and not raw.startswith('00') and len(digits) == 9:
        digits = f'48{digits}'

    if not digits or digits.startswith('0'):
        raise DjangoValidationError(PHONE_INVALID, code='invalid')

    e164 = f'+{digits}'
    if not _E164.match(e164):
        raise DjangoValidationError(PHONE_INVALID, code='invalid')

    return e164
