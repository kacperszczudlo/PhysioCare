from __future__ import annotations

import re

from django.core.exceptions import ValidationError as DjangoValidationError

PWZF_REQUIRED: str = 'Podaj numer PWZFz.'
PWZF_INVALID: str = (
    'Podaj prawidłowy numer PWZFz - dokładnie 5 cyfr (np. 12345).'
)
PWZF_TOO_LONG: str = 'Numer PWZFz może mieć co najwyżej 20 znaków.'
PWZF_TAKEN: str = (
    'Konto z tym numerem PWZFz już istnieje. Zaloguj się lub użyj innego numeru.'
)

PWZF_FIELD_ERRORS: dict[str, str] = {
    'blank': PWZF_REQUIRED,
    'required': PWZF_REQUIRED,
    'null': PWZF_REQUIRED,
    'max_length': PWZF_TOO_LONG,
    'invalid': PWZF_INVALID,
}

_PWZF_PATTERN: re.Pattern[str] = re.compile(r'^\d{5}$')
_PREFIX_PATTERN: re.Pattern[str] = re.compile(
    r'^(?:pwzfz|pwzf)(?:\s*nr\.?|\s*nr|:|-)?\s*',
    re.IGNORECASE,
)


def normalize_and_validate_pwzf(value: str | None) -> str:
    """Normalizuje oraz waliduje numer PWZFz (dokładnie 5 cyfr KIF).

    Akceptuje formy z pieczątek, np. "PWZFz nr 12345" i zwraca znormalizowany ciąg "12345".

    Args:
        value (str | None): Weryfikowany numer PWZFz.

    Returns:
        str: Znormalizowany 5-cyfrowy numer PWZFz.

    Raises:
        DjangoValidationError: Gdy numer jest pusty, przekracza 20 znaków lub ma nieprawidłowy format.
    """
    if value is not None and not isinstance(value, str):
        raise DjangoValidationError(PWZF_INVALID, code='invalid')

    if value is None or value.strip() == '':
        raise DjangoValidationError(PWZF_REQUIRED, code='required')

    raw = str(value).strip()
    if len(raw) > 20:
        raise DjangoValidationError(PWZF_TOO_LONG, code='max_length')

    cleaned = _PREFIX_PATTERN.sub('', raw)
    digits = re.sub(r'[\s\-]', '', cleaned)
    if not _PWZF_PATTERN.fullmatch(digits):
        raise DjangoValidationError(PWZF_INVALID, code='invalid')

    return digits
