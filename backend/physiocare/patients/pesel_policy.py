"""PESEL validation with Polish user-facing messages."""

from __future__ import annotations

import re
from datetime import date

from django.core.exceptions import ValidationError as DjangoValidationError

PESEL_REQUIRED = 'Podaj numer PESEL.'
PESEL_INVALID_FORMAT = 'PESEL musi składać się z dokładnie 11 cyfr.'
PESEL_INVALID_CHECKSUM = 'Numer PESEL jest nieprawidłowy (błędna suma kontrolna).'
PESEL_INVALID_DATE = 'Numer PESEL jest nieprawidłowy (błędna data urodzenia).'
PESEL_TOO_LONG = 'Numer PESEL może mieć co najwyżej 11 znaków.'

PESEL_FIELD_ERRORS = {
    'blank': PESEL_REQUIRED,
    'required': PESEL_REQUIRED,
    'null': PESEL_REQUIRED,
    'max_length': PESEL_TOO_LONG,
    'invalid': PESEL_INVALID_FORMAT,
}

_PESEL_DIGITS = re.compile(r'^\d{11}$')
_PESEL_WEIGHTS = (1, 3, 7, 9, 1, 3, 7, 9, 1, 3)


def _decode_pesel_birth_date(digits: str) -> date | None:
    """Extract birth date from PESEL or return None if impossible."""
    year = int(digits[0:2])
    month = int(digits[2:4])
    day = int(digits[4:6])

    if 1 <= month <= 12:
        century = 1900
    elif 21 <= month <= 32:
        century = 2000
        month -= 20
    elif 41 <= month <= 52:
        century = 2100
        month -= 40
    elif 61 <= month <= 72:
        century = 2200
        month -= 60
    elif 81 <= month <= 92:
        century = 1800
        month -= 80
    else:
        return None

    try:
        return date(century + year, month, day)
    except ValueError:
        return None


def _has_valid_checksum(digits: str) -> bool:
    total = sum(
        weight * int(digit)
        for weight, digit in zip(_PESEL_WEIGHTS, digits[:10], strict=True)
    )
    control = (10 - (total % 10)) % 10
    return control == int(digits[10])


def normalize_and_validate_pesel(value: str | None, *, allow_blank: bool = True) -> str | None:
    """Normalize and validate PESEL. Blank/None allowed when allow_blank=True."""
    if value is None:
        if allow_blank:
            return None
        raise DjangoValidationError(PESEL_REQUIRED, code='required')

    raw = str(value).strip()
    if raw == '':
        if allow_blank:
            return None
        raise DjangoValidationError(PESEL_REQUIRED, code='required')

    if len(raw) > 11:
        raise DjangoValidationError(PESEL_TOO_LONG, code='max_length')

    if not _PESEL_DIGITS.fullmatch(raw):
        raise DjangoValidationError(PESEL_INVALID_FORMAT, code='invalid')

    if _decode_pesel_birth_date(raw) is None:
        raise DjangoValidationError(PESEL_INVALID_DATE, code='invalid_date')

    if not _has_valid_checksum(raw):
        raise DjangoValidationError(PESEL_INVALID_CHECKSUM, code='invalid_checksum')

    return raw
