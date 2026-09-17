from __future__ import annotations

import re

from django.core.exceptions import ValidationError as DjangoValidationError

MIN_NAME_LENGTH: int = 2
MAX_NAME_LENGTH: int = 100
MIN_ADDRESS_LENGTH: int = 5
MAX_ADDRESS_LENGTH: int = 300
MAX_BIO_LENGTH: int = 2000
MAX_COURSES_COUNT: int = 50
MAX_COURSE_NAME_LENGTH: int = 200
MAX_ICD10_LENGTH: int = 10
MAX_DOSAGE_LENGTH: int = 100
MIN_THERAPY_DURATION_MINUTES: int = 5
MAX_THERAPY_DURATION_MINUTES: int = 480
MAX_THERAPY_NAME_LENGTH: int = 100
MAX_EXERCISE_TITLE_LENGTH: int = 200

NAME_REQUIRED: str = 'Podaj imię.'
LAST_NAME_REQUIRED: str = 'Podaj nazwisko.'
NAME_TOO_SHORT: str = f'Imię musi mieć co najmniej {MIN_NAME_LENGTH} znaki.'
LAST_NAME_TOO_SHORT: str = f'Nazwisko musi mieć co najmniej {MIN_NAME_LENGTH} znaki.'
NAME_TOO_LONG: str = f'Imię może mieć co najwyżej {MAX_NAME_LENGTH} znaków.'
LAST_NAME_TOO_LONG: str = f'Nazwisko może mieć co najwyżej {MAX_NAME_LENGTH} znaków.'
NAME_INVALID: str = (
    'Imię może zawierać litery, spacje, myślnik i apostrof '
    '(np. Anna, Jean-Pierre, O\'Brien).'
)
LAST_NAME_INVALID: str = (
    'Nazwisko może zawierać litery, spacje, myślnik i apostrof '
    '(np. Kowalska, Nowak-Wiśniewska).'
)

ADDRESS_TOO_LONG: str = f'Adres może mieć co najwyżej {MAX_ADDRESS_LENGTH} znaków.'
ADDRESS_TOO_SHORT: str = 'Adres jest zbyt krótki - podaj ulicę i miejscowość.'
BIO_TOO_LONG: str = f'Opis profilu może mieć co najwyżej {MAX_BIO_LENGTH} znaków.'
COURSE_REQUIRED: str = 'Nazwa kursu nie może być pusta.'
COURSE_TOO_LONG: str = f'Nazwa kursu może mieć co najwyżej {MAX_COURSE_NAME_LENGTH} znaków.'
COURSES_INVALID: str = 'Lista kursów musi być tablicą tekstów.'
COURSES_TOO_MANY: str = f'Możesz dodać co najwyżej {MAX_COURSES_COUNT} kursów.'

ICD10_INVALID: str = (
    'Podaj prawidłowy kod ICD-10 (np. M54.5, S83.4) albo pozostaw puste.'
)
ICD10_TOO_LONG: str = f'Kod ICD-10 może mieć co najwyżej {MAX_ICD10_LENGTH} znaków.'

DOSAGE_REQUIRED: str = 'Podaj dawkowanie ćwiczenia.'
DOSAGE_TOO_LONG: str = f'Dawkowanie może mieć co najwyżej {MAX_DOSAGE_LENGTH} znaków.'

PREP_TOO_LONG: str = 'Instrukcje przygotowania mogą mieć co najwyżej 2000 znaków.'
NOTE_TOO_LONG: str = 'Notatka może mieć co najwyżej 5000 znaków.'
NOTE_REQUIRED: str = 'Treść notatki nie może być pusta.'
CANCEL_REASON_TOO_LONG: str = 'Powód anulowania może mieć co najwyżej 500 znaków.'
SUMMARY_TOO_LONG: str = 'Podsumowanie może mieć co najwyżej 5000 znaków.'

TITLE_REQUIRED: str = 'Podaj tytuł ćwiczenia.'
TITLE_TOO_LONG: str = f'Tytuł może mieć co najwyżej {MAX_EXERCISE_TITLE_LENGTH} znaków.'
INSTRUCTION_TOO_LONG: str = 'Instrukcja może mieć co najwyżej 5000 znaków.'

COLOR_HEX_INVALID: str = 'Kolor musi być w formacie #RRGGBB (np. #2A9D8F).'
THERAPY_NAME_REQUIRED: str = 'Podaj nazwę typu terapii.'
THERAPY_NAME_TOO_LONG: str = f'Nazwa typu terapii może mieć co najwyżej {MAX_THERAPY_NAME_LENGTH} znaków.'
DURATION_INVALID: str = f'Czas trwania musi być liczbą od {MIN_THERAPY_DURATION_MINUTES} do {MAX_THERAPY_DURATION_MINUTES} minut.'

DOCUMENT_TITLE_REQUIRED: str = 'Podaj tytuł dokumentu.'
DOCUMENT_TITLE_TOO_LONG: str = 'Tytuł dokumentu może mieć co najwyżej 200 znaków.'

_NAME_PATTERN: re.Pattern[str] = re.compile(
    r"^[A-Za-zÀ-ÖØ-öø-ÿĄąĆćĘęŁłŃńÓóŚśŹźŻż]+"
    r"(?:[ '\-][A-Za-zÀ-ÖØ-öø-ÿĄąĆćĘęŁłŃńÓóŚśŹźŻż]+)*$"
)
_ICD10_PATTERN: re.Pattern[str] = re.compile(r'^[A-TV-Z][0-9]{2}(?:\.[0-9A-TV-Z]{1,4})?$', re.IGNORECASE)
_COLOR_HEX_PATTERN: re.Pattern[str] = re.compile(r'^#[0-9A-Fa-f]{6}$')


def normalize_and_validate_name(
    value: str | None,
    *,
    required_message: str = NAME_REQUIRED,
    too_short_message: str = NAME_TOO_SHORT,
    too_long_message: str = NAME_TOO_LONG,
    invalid_message: str = NAME_INVALID,
) -> str:
    """Normalizuje i waliduje nazwisko lub imię.

    Args:
        value: Wartość tekstowa do walidacji.
        required_message: Komunikat w przypadku braku wartości.
        too_short_message: Komunikat, gdy tekst jest za krótki.
        too_long_message: Komunikat, gdy tekst jest za długi.
        invalid_message: Komunikat, gdy tekst zawiera niedozwolone znaki.

    Returns:
        Znormalizowany ciąg znaków.

    Raises:
        DjangoValidationError: Gdy walidacja się nie powiedzie.
    """
    if value is not None and not isinstance(value, str):
        raise DjangoValidationError(invalid_message, code='invalid')

    if value is None or value.strip() == '':
        raise DjangoValidationError(required_message, code='required')

    name = ' '.join(value.split())
    if len(name) < MIN_NAME_LENGTH:
        raise DjangoValidationError(too_short_message, code='min_length')
    if len(name) > MAX_NAME_LENGTH:
        raise DjangoValidationError(too_long_message, code='max_length')
    if not _NAME_PATTERN.fullmatch(name):
        raise DjangoValidationError(invalid_message, code='invalid')
    return name


def normalize_and_validate_first_name(value: str | None) -> str:
    """Normalizuje i waliduje imię użytkownika.

    Args:
        value: Imię do walidacji.

    Returns:
        Znormalizowane imię.

    Raises:
        DjangoValidationError: Gdy imię jest nieprawidłowe.
    """
    return normalize_and_validate_name(
        value,
        required_message=NAME_REQUIRED,
        too_short_message=NAME_TOO_SHORT,
        too_long_message=NAME_TOO_LONG,
        invalid_message=NAME_INVALID,
    )


def normalize_and_validate_last_name(value: str | None) -> str:
    """Normalizuje i waliduje nazwisko użytkownika.

    Args:
        value: Nazwisko do walidacji.

    Returns:
        Znormalizowane nazwisko.

    Raises:
        DjangoValidationError: Gdy nazwisko jest nieprawidłowe.
    """
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
    """Normalizuje i waliduje adres.

    Args:
        value: Adres do walidacji.
        allow_blank: Czy adres może być pusty.

    Returns:
        Znormalizowany adres.

    Raises:
        DjangoValidationError: Gdy adres nie spełnia wymogów długości.
    """
    if value is not None and not isinstance(value, str):
        raise DjangoValidationError(ADDRESS_TOO_SHORT, code='invalid')

    if value is None or value.strip() == '':
        if allow_blank:
            return ''
        raise DjangoValidationError('Podaj adres.', code='required')

    address = ' '.join(value.split())
    if len(address) > MAX_ADDRESS_LENGTH:
        raise DjangoValidationError(ADDRESS_TOO_LONG, code='max_length')
    if len(address) < MIN_ADDRESS_LENGTH:
        raise DjangoValidationError(ADDRESS_TOO_SHORT, code='min_length')
    return address


def normalize_and_validate_bio(value: str | None, *, allow_blank: bool = True) -> str:
    """Normalizuje i waliduje opis profilu (bio).

    Args:
        value: Opis profilu do walidacji.
        allow_blank: Czy opis może być pusty.

    Returns:
        Znormalizowany opis profilu.

    Raises:
        DjangoValidationError: Gdy opis jest zbyt długi lub wymagany a brakujący.
    """
    if value is not None and not isinstance(value, str):
        raise DjangoValidationError(BIO_TOO_LONG, code='invalid')

    if value is None:
        return '' if allow_blank else (_raise_required('Podaj opis profilu.'))
    bio = value.strip()
    if bio == '':
        return '' if allow_blank else (_raise_required('Podaj opis profilu.'))
    if len(bio) > MAX_BIO_LENGTH:
        raise DjangoValidationError(BIO_TOO_LONG, code='max_length')
    return bio


def normalize_and_validate_courses(value: list[str] | None) -> list[str]:
    """Normalizuje i waliduje listę ukończonych kursów.

    Args:
        value: Lista nazw kursów.

    Returns:
        Lista znormalizowanych nazw kursów.

    Raises:
        DjangoValidationError: Gdy format jest niepoprawny, nazwa za długa lub zbyt wiele kursów.
    """
    if value is None:
        return []
    if not isinstance(value, list):
        raise DjangoValidationError(COURSES_INVALID, code='invalid')
    if len(value) > MAX_COURSES_COUNT:
        raise DjangoValidationError(COURSES_TOO_MANY, code='max_length')

    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise DjangoValidationError(COURSES_INVALID, code='invalid')
        course = ' '.join(item.split())
        if not course:
            raise DjangoValidationError(COURSE_REQUIRED, code='blank')
        if len(course) > MAX_COURSE_NAME_LENGTH:
            raise DjangoValidationError(COURSE_TOO_LONG, code='max_length')
        normalized.append(course)
    return normalized


def normalize_and_validate_icd10(value: str | None, *, allow_blank: bool = True) -> str:
    """Normalizuje i waliduje kod rozpoznania ICD-10.

    Args:
        value: Kod ICD-10 do walidacji.
        allow_blank: Czy kod może być pusty.

    Returns:
        Znormalizowany wielkimi literami kod ICD-10.

    Raises:
        DjangoValidationError: Gdy kod ma niepoprawny format lub jest zbyt długi.
    """
    if value is not None and not isinstance(value, str):
        raise DjangoValidationError(ICD10_INVALID, code='invalid')

    if value is None or value.strip() == '':
        if allow_blank:
            return ''
        raise DjangoValidationError('Podaj kod ICD-10.', code='required')

    code = value.strip().upper()
    if len(code) > MAX_ICD10_LENGTH:
        raise DjangoValidationError(ICD10_TOO_LONG, code='max_length')
    if not _ICD10_PATTERN.fullmatch(code):
        raise DjangoValidationError(ICD10_INVALID, code='invalid')
    return code


def normalize_and_validate_dosage(value: str | None, *, allow_blank: bool = False) -> str:
    """Normalizuje i waliduje opis dawkowania ćwiczenia.

    Args:
        value: Opis dawkowania do walidacji.
        allow_blank: Czy dawkowanie może być puste.

    Returns:
        Znormalizowany ciąg znaków opisujący dawkowanie.

    Raises:
        DjangoValidationError: Gdy dawkowanie jest puste lub zbyt długie.
    """
    if value is not None and not isinstance(value, str):
        raise DjangoValidationError(DOSAGE_TOO_LONG, code='invalid')

    if value is None or value.strip() == '':
        if allow_blank:
            return ''
        raise DjangoValidationError(DOSAGE_REQUIRED, code='required')
    dosage = ' '.join(value.split())
    if len(dosage) > MAX_DOSAGE_LENGTH:
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
    """Normalizuje i waliduje opcjonalny tekst z ograniczeniem długości.

    Args:
        value: Tekst do walidacji.
        max_length: Maksymalna dozwolona długość.
        too_long_message: Komunikat w przypadku przekroczenia długości.
        allow_blank: Czy tekst może być pusty.
        required_message: Komunikat w przypadku braku wymaganego tekstu.

    Returns:
        Znormalizowany tekst.

    Raises:
        DjangoValidationError: Gdy tekst nie spełnia wymogów.
    """
    if value is not None and not isinstance(value, str):
        raise DjangoValidationError(too_long_message, code='invalid')

    if value is None or value.strip() == '':
        if allow_blank:
            return ''
        raise DjangoValidationError(
            required_message or 'To pole jest wymagane.',
            code='required',
        )
    text = value.strip()
    if len(text) > max_length:
        raise DjangoValidationError(too_long_message, code='max_length')
    return text


def normalize_and_validate_color_hex(value: str | None) -> str:
    """Normalizuje i waliduje kod koloru w formacie HEX (#RRGGBB).

    Args:
        value: Kod koloru do walidacji.

    Returns:
        Znormalizowany kod koloru drukowanymi literami.

    Raises:
        DjangoValidationError: Gdy format koloru jest niepoprawny.
    """
    if value is not None and not isinstance(value, str):
        raise DjangoValidationError(COLOR_HEX_INVALID, code='invalid')

    if value is None or value.strip() == '':
        raise DjangoValidationError(COLOR_HEX_INVALID, code='required')
    color = value.strip()
    if not _COLOR_HEX_PATTERN.fullmatch(color):
        raise DjangoValidationError(COLOR_HEX_INVALID, code='invalid')
    return color.upper()


def normalize_and_validate_therapy_name(value: str | None) -> str:
    """Normalizuje i waliduje nazwę typu terapii.

    Args:
        value: Nazwa terapii do walidacji.

    Returns:
        Znormalizowaną nazwę terapii.

    Raises:
        DjangoValidationError: Gdy nazwa jest pusta lub za długa.
    """
    if value is not None and not isinstance(value, str):
        raise DjangoValidationError(THERAPY_NAME_REQUIRED, code='invalid')

    if value is None or value.strip() == '':
        raise DjangoValidationError(THERAPY_NAME_REQUIRED, code='required')
    name = ' '.join(value.split())
    if len(name) > MAX_THERAPY_NAME_LENGTH:
        raise DjangoValidationError(THERAPY_NAME_TOO_LONG, code='max_length')
    return name


def normalize_and_validate_duration_min(value: int | str | float | None) -> int:
    """Normalizuje i waliduje czas trwania terapii w minutach.

    Args:
        value: Czas trwania w minutach.

    Returns:
        Czas trwania w minutach jako liczba całkowita.

    Raises:
        DjangoValidationError: Gdy wartość nie jest poprawną liczbą z wymaganego zakresu.
    """
    if value is not None and not isinstance(value, (int, float, str)):
        raise DjangoValidationError(DURATION_INVALID, code='invalid')
    try:
        duration = int(value)
    except (TypeError, ValueError) as exc:
        raise DjangoValidationError(DURATION_INVALID, code='invalid') from exc
    if duration < MIN_THERAPY_DURATION_MINUTES or duration > MAX_THERAPY_DURATION_MINUTES:
        raise DjangoValidationError(DURATION_INVALID, code='invalid')
    return duration


def normalize_and_validate_exercise_title(value: str | None) -> str:
    """Normalizuje i waliduje tytuł ćwiczenia.

    Args:
        value: Tytuł ćwiczenia do walidacji.

    Returns:
        Znormalizowany tytuł ćwiczenia.

    Raises:
        DjangoValidationError: Gdy tytuł jest pusty lub zbyt długi.
    """
    if value is not None and not isinstance(value, str):
        raise DjangoValidationError(TITLE_REQUIRED, code='invalid')

    if value is None or value.strip() == '':
        raise DjangoValidationError(TITLE_REQUIRED, code='required')
    title = ' '.join(value.split())
    if len(title) > MAX_EXERCISE_TITLE_LENGTH:
        raise DjangoValidationError(TITLE_TOO_LONG, code='max_length')
    return title


def _raise_required(message: str) -> None:
    """Rzuca wyjątek DjangoValidationError wskazujący na brak wymaganego pola.

    Args:
        message: Treść komunikatu o błędzie.

    Raises:
        DjangoValidationError: Zawsze zgłasza błąd z podanym komunikatem.
    """
    raise DjangoValidationError(message, code='required')
