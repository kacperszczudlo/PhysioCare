"""PWZFz (physiotherapist license) validation with Polish messages."""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError as DjangoValidationError

PWZF_REQUIRED = 'Podaj numer PWZFz.'
PWZF_INVALID = (
    'Podaj prawidłowy numer PWZFz - dokładnie 5 cyfr (np. 12345).'
)
PWZF_TOO_LONG = 'Numer PWZFz może mieć co najwyżej 20 znaków.'
PWZF_TAKEN = (
    'Konto z tym numerem PWZFz już istnieje. Zaloguj się lub użyj innego numeru.'
)

PWZF_FIELD_ERRORS = {
    'blank': PWZF_REQUIRED,
    'required': PWZF_REQUIRED,
    'null': PWZF_REQUIRED,
    'max_length': PWZF_TOO_LONG,
    'invalid': PWZF_INVALID,
}

_PWZF_PATTERN = re.compile(r'^\d{5}$')
_PREFIX_PATTERN = re.compile(
    r'^(?:pwzfz|pwzf)(?:\s*nr\.?|\s*nr|:|-)?\s*',
    re.IGNORECASE,
)


def normalize_and_validate_pwzf(value: str | None) -> str:
    """Normalize and validate PWZFz: exactly 5 digits (KIF).

    Accepts common stamp forms like ``PWZFz nr 12345`` and stores ``12345``.
    """
    if value is None or str(value).strip() == '':
        raise DjangoValidationError(PWZF_REQUIRED, code='required')

    raw = str(value).strip()
    if len(raw) > 20:
        raise DjangoValidationError(PWZF_TOO_LONG, code='max_length')

    cleaned = _PREFIX_PATTERN.sub('', raw)
    digits = re.sub(r'[\s\-]', '', cleaned)
    if not _PWZF_PATTERN.fullmatch(digits):
        raise DjangoValidationError(PWZF_INVALID, code='invalid')

    return digits
