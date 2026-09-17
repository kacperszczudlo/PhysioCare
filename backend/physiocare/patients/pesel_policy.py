from __future__ import annotations

import re
from datetime import date

from django.core.exceptions import ValidationError as DjangoValidationError

PESEL_REQUIRED: str = 'Podaj numer PESEL.'
PESEL_INVALID_FORMAT: str = 'PESEL musi składać się z dokładnie 11 cyfr.'
PESEL_INVALID_CHECKSUM: str = 'Numer PESEL jest nieprawidłowy (błędna suma kontrolna).'
PESEL_INVALID_DATE: str = 'Numer PESEL jest nieprawidłowy (błędna data urodzenia).'
PESEL_TOO_LONG: str = 'Numer PESEL może mieć co najwyżej 11 znaków.'

PESEL_FIELD_ERRORS: dict[str, str] = {
    'blank': PESEL_REQUIRED,
    'required': PESEL_REQUIRED,
    'null': PESEL_REQUIRED,
    'max_length': PESEL_TOO_LONG,
    'invalid': PESEL_INVALID_FORMAT,
}

_PESEL_DIGITS: re.Pattern[str] = re.compile(r'^\d{11}$')
_PESEL_WEIGHTS: tuple[int, ...] = (1, 3, 7, 9, 1, 3, 7, 9, 1, 3)


def _decode_pesel_birth_date(digits: str) -> date | None:
    """Wyciąga datę urodzenia z ciągu cyfr numeru PESEL lub zwraca None.

    Args:
        digits (str): Ciąg 11 cyfr numeru PESEL.

    Returns:
        date | None: Wyliczona data urodzenia lub None, jeśli data/kod jest niepoprawny.

    Raises:
        TypeError: Gdy parametr digits nie jest ciągiem znaków.
    """
    if not isinstance(digits, str):
        raise TypeError('Parametr digits musi być ciągiem znaków.')

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
    """Sprawdza poprawność cyfry kontrolnej numeru PESEL.

    Args:
        digits (str): Ciąg 11 cyfr numeru PESEL.

    Returns:
        bool: True jeśli suma kontrolna jest poprawna, False w przeciwnym razie.

    Raises:
        TypeError: Gdy parametr digits nie jest ciągiem znaków.
    """
    if not isinstance(digits, str):
        raise TypeError('Parametr digits musi być ciągiem znaków.')
    if len(digits) != 11:
        return False
    total = sum(
        weight * int(digit)
        for weight, digit in zip(_PESEL_WEIGHTS, digits[:10], strict=True)
    )
    control = (10 - (total % 10)) % 10
    return control == int(digits[10])


def normalize_and_validate_pesel(value: str | None, *, allow_blank: bool = True) -> str | None:
    """Normalizuje oraz waliduje poprawność numeru PESEL.

    Args:
        value (str | None): Weryfikowany numer PESEL.
        allow_blank (bool): Czy pusty numer PESEL jest dozwolony.

    Returns:
        str | None: Znormalizowany numer PESEL lub None.

    Raises:
        DjangoValidationError: Gdy format, data lub suma kontrolna są nieprawidłowe.
        TypeError: Gdy parametr allow_blank nie jest wartością logiczną (bool).
    """
    if not isinstance(allow_blank, bool):
        raise TypeError('Parametr allow_blank musi być wartością logiczną (bool).')

    if value is not None and not isinstance(value, str):
        raise DjangoValidationError(PESEL_INVALID_FORMAT, code='invalid')

    if value is None:
        if allow_blank:
            return None
        raise DjangoValidationError(PESEL_REQUIRED, code='required')

    raw = value.strip()
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

