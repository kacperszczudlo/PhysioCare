"""Shared field validation policies with Polish user-facing messages."""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError as DjangoValidationError

NAME_REQUIRED = 'Podaj imię.'
LAST_NAME_REQUIRED = 'Podaj nazwisko.'
NAME_TOO_SHORT = 'Imię musi mieć co najmniej 2 znaki.'
LAST_NAME_TOO_SHORT = 'Nazwisko musi mieć co najmniej 2 znaki.'
NAME_TOO_LONG = 'Imię może mieć co najwyżej 100 znaków.'
LAST_NAME_TOO_LONG = 'Nazwisko może mieć co najwyżej 100 znaków.'
NAME_INVALID = (
    'Imię może zawierać litery, spacje, myślnik i apostrof '
    '(np. Anna, Jean-Pierre, O\'Brien).'
)
LAST_NAME_INVALID = (
    'Nazwisko może zawierać litery, spacje, myślnik i apostrof '
    '(np. Kowalska, Nowak-Wiśniewska).'
)

ADDRESS_TOO_LONG = 'Adres może mieć co najwyżej 300 znaków.'
ADDRESS_TOO_SHORT = 'Adres jest zbyt krótki - podaj ulicę i miejscowość.'
BIO_TOO_LONG = 'Opis profilu może mieć co najwyżej 2000 znaków.'
COURSE_REQUIRED = 'Nazwa kursu nie może być pusta.'
COURSE_TOO_LONG = 'Nazwa kursu może mieć co najwyżej 200 znaków.'
COURSES_INVALID = 'Lista kursów musi być tablicą tekstów.'
COURSES_TOO_MANY = 'Możesz dodać co najwyżej 50 kursów.'

ICD10_INVALID = (
    'Podaj prawidłowy kod ICD-10 (np. M54.5, S83.4) albo pozostaw puste.'
)
ICD10_TOO_LONG = 'Kod ICD-10 może mieć co najwyżej 10 znaków.'

DOSAGE_REQUIRED = 'Podaj dawkowanie ćwiczenia.'
DOSAGE_TOO_LONG = 'Dawkowanie może mieć co najwyżej 100 znaków.'

PREP_TOO_LONG = 'Instrukcje przygotowania mogą mieć co najwyżej 2000 znaków.'
NOTE_TOO_LONG = 'Notatka może mieć co najwyżej 5000 znaków.'
NOTE_REQUIRED = 'Treść notatki nie może być pusta.'
CANCEL_REASON_TOO_LONG = 'Powód anulowania może mieć co najwyżej 500 znaków.'
SUMMARY_TOO_LONG = 'Podsumowanie może mieć co najwyżej 5000 znaków.'

TITLE_REQUIRED = 'Podaj tytuł ćwiczenia.'
TITLE_TOO_LONG = 'Tytuł może mieć co najwyżej 200 znaków.'
INSTRUCTION_TOO_LONG = 'Instrukcja może mieć co najwyżej 5000 znaków.'

COLOR_HEX_INVALID = 'Kolor musi być w formacie #RRGGBB (np. #2A9D8F).'
THERAPY_NAME_REQUIRED = 'Podaj nazwę typu terapii.'
THERAPY_NAME_TOO_LONG = 'Nazwa typu terapii może mieć co najwyżej 100 znaków.'
DURATION_INVALID = 'Czas trwania musi być liczbą od 5 do 480 minut.'

DOCUMENT_TITLE_REQUIRED = 'Podaj tytuł dokumentu.'
DOCUMENT_TITLE_TOO_LONG = 'Tytuł dokumentu może mieć co najwyżej 200 znaków.'

_NAME_PATTERN = re.compile(
    r"^[A-Za-zÀ-ÖØ-öø-ÿĄąĆćĘęŁłŃńÓóŚśŹźŻż]+"
    r"(?:[ '\-][A-Za-zÀ-ÖØ-öø-ÿĄąĆćĘęŁłŃńÓóŚśŹźŻż]+)*$"
)
_ICD10_PATTERN = re.compile(r'^[A-TV-Z][0-9]{2}(?:\.[0-9A-TV-Z]{1,4})?$', re.IGNORECASE)
_COLOR_HEX_PATTERN = re.compile(r'^#[0-9A-Fa-f]{6}$')


def normalize_and_validate_name(
    value: str | None,
    *,
    required_message: str = NAME_REQUIRED,
    too_short_message: str = NAME_TOO_SHORT,
    too_long_message: str = NAME_TOO_LONG,
    invalid_message: str = NAME_INVALID,
) -> str:
    if value is None or str(value).strip() == '':
        raise DjangoValidationError(required_message, code='required')

    name = ' '.join(str(value).split())
    if len(name) < 2:
        raise DjangoValidationError(too_short_message, code='min_length')
    if len(name) > 100:
        raise DjangoValidationError(too_long_message, code='max_length')
    if not _NAME_PATTERN.fullmatch(name):
        raise DjangoValidationError(invalid_message, code='invalid')
    return name


def normalize_and_validate_first_name(value: str | None) -> str:
    return normalize_and_validate_name(
        value,
        required_message=NAME_REQUIRED,
        too_short_message=NAME_TOO_SHORT,
        too_long_message=NAME_TOO_LONG,
        invalid_message=NAME_INVALID,
    )


def normalize_and_validate_last_name(value: str | None) -> str:
    return normalize_and_validate_name(
        value,
        required_message=LAST_NAME_REQUIRED,
        too_short_message=LAST_NAME_TOO_SHORT,
        too_long_message=LAST_NAME_TOO_LONG,
        invalid_message=LAST_NAME_INVALID,
    )


def normalize_and_validate_address(
    value: str | None,
    *,
    allow_blank: bool = True,
) -> str:
    if value is None or str(value).strip() == '':
        if allow_blank:
            return ''
        raise DjangoValidationError('Podaj adres.', code='required')

    address = ' '.join(str(value).split())
    if len(address) > 300:
        raise DjangoValidationError(ADDRESS_TOO_LONG, code='max_length')
    if len(address) < 5:
        raise DjangoValidationError(ADDRESS_TOO_SHORT, code='min_length')
    return address


def normalize_and_validate_bio(value: str | None, *, allow_blank: bool = True) -> str:
    if value is None:
        return '' if allow_blank else (_raise_required('Podaj opis profilu.'))
    bio = str(value).strip()
    if bio == '':
        return '' if allow_blank else (_raise_required('Podaj opis profilu.'))
    if len(bio) > 2000:
        raise DjangoValidationError(BIO_TOO_LONG, code='max_length')
    return bio


def normalize_and_validate_courses(value) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise DjangoValidationError(COURSES_INVALID, code='invalid')
    if len(value) > 50:
        raise DjangoValidationError(COURSES_TOO_MANY, code='max_length')

    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise DjangoValidationError(COURSES_INVALID, code='invalid')
        course = ' '.join(item.split())
        if not course:
            raise DjangoValidationError(COURSE_REQUIRED, code='blank')
        if len(course) > 200:
            raise DjangoValidationError(COURSE_TOO_LONG, code='max_length')
        normalized.append(course)
    return normalized


def normalize_and_validate_icd10(value: str | None, *, allow_blank: bool = True) -> str:
    if value is None or str(value).strip() == '':
        if allow_blank:
            return ''
        raise DjangoValidationError('Podaj kod ICD-10.', code='required')

    code = str(value).strip().upper()
    if len(code) > 10:
        raise DjangoValidationError(ICD10_TOO_LONG, code='max_length')
    if not _ICD10_PATTERN.fullmatch(code):
        raise DjangoValidationError(ICD10_INVALID, code='invalid')
    return code


def normalize_and_validate_dosage(value: str | None, *, allow_blank: bool = False) -> str:
    if value is None or str(value).strip() == '':
        if allow_blank:
            return ''
        raise DjangoValidationError(DOSAGE_REQUIRED, code='required')
    dosage = ' '.join(str(value).split())
    if len(dosage) > 100:
        raise DjangoValidationError(DOSAGE_TOO_LONG, code='max_length')
    return dosage


def normalize_optional_text(
    value: str | None,
    *,
    max_length: int,
    too_long_message: str,
    allow_blank: bool = True,
    required_message: str | None = None,
) -> str:
    if value is None or str(value).strip() == '':
        if allow_blank:
            return ''
        raise DjangoValidationError(
            required_message or 'To pole jest wymagane.',
            code='required',
        )
    text = str(value).strip()
    if len(text) > max_length:
        raise DjangoValidationError(too_long_message, code='max_length')
    return text


def normalize_and_validate_color_hex(value: str | None) -> str:
    if value is None or str(value).strip() == '':
        raise DjangoValidationError(COLOR_HEX_INVALID, code='required')
    color = str(value).strip()
    if not _COLOR_HEX_PATTERN.fullmatch(color):
        raise DjangoValidationError(COLOR_HEX_INVALID, code='invalid')
    return color.upper()


def normalize_and_validate_therapy_name(value: str | None) -> str:
    if value is None or str(value).strip() == '':
        raise DjangoValidationError(THERAPY_NAME_REQUIRED, code='required')
    name = ' '.join(str(value).split())
    if len(name) > 100:
        raise DjangoValidationError(THERAPY_NAME_TOO_LONG, code='max_length')
    return name


def normalize_and_validate_duration_min(value) -> int:
    try:
        duration = int(value)
    except (TypeError, ValueError) as exc:
        raise DjangoValidationError(DURATION_INVALID, code='invalid') from exc
    if duration < 5 or duration > 480:
        raise DjangoValidationError(DURATION_INVALID, code='invalid')
    return duration


def normalize_and_validate_exercise_title(value: str | None) -> str:
    if value is None or str(value).strip() == '':
        raise DjangoValidationError(TITLE_REQUIRED, code='required')
    title = ' '.join(str(value).split())
    if len(title) > 200:
        raise DjangoValidationError(TITLE_TOO_LONG, code='max_length')
    return title


def _raise_required(message: str):
    raise DjangoValidationError(message, code='required')
