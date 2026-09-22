from datetime import date

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError

from patients.pesel_policy import (
    PESEL_INVALID_CHECKSUM,
    PESEL_INVALID_DATE,
    PESEL_INVALID_FORMAT,
    PESEL_REQUIRED,
    PESEL_TOO_LONG,
    _decode_pesel_birth_date,
    normalize_and_validate_pesel,
)


@pytest.mark.parametrize(
    'pesel,expected_date',
    [
        ('92071304259', date(1992, 7, 13)),
        ('02271501248', date(2002, 7, 15)),
        ('80811501235', date(1880, 1, 15)),
        ('15451201234', date(2115, 5, 12)),
        ('30652001232', date(2230, 5, 20)),
    ],
)
def test_decode_pesel_birth_date_valid(pesel: str, expected_date: date) -> None:
    """Sprawdza poprawne dekodowanie daty urodzenia z numeru PESEL dla różnych stuleci."""
    # Assert
    assert _decode_pesel_birth_date(pesel) == expected_date


def test_decode_pesel_birth_date_invalid_month() -> None:
    """Sprawdza powrót None przy nieprawidłowym kodowaniu miesiąca w PESEL."""
    # Assert
    assert _decode_pesel_birth_date('92131304251') is None


def test_decode_pesel_birth_date_invalid_day() -> None:
    """Sprawdza powrót None przy nieprawidłowej liczbie dni dla podanego miesiąca w PESEL."""
    # Assert
    assert _decode_pesel_birth_date('92023104251') is None


@pytest.mark.parametrize(
    'valid_pesel',
    [
        '92071304259',
        '02271501248',
    ],
)
def test_valid_pesel_normalization(valid_pesel: str) -> None:
    """Sprawdza poprawną normalizację i walidację prawidłowego numeru PESEL."""
    # Assert
    assert normalize_and_validate_pesel(valid_pesel) == valid_pesel
    assert normalize_and_validate_pesel(f'  {valid_pesel}  ') == valid_pesel


@pytest.mark.parametrize(
    'blank_input',
    [None, '', '   '],
)
def test_pesel_allow_blank_true(blank_input: str | None) -> None:
    """Sprawdza akceptację pustego numeru PESEL, gdy parametr allow_blank jest włączony."""
    # Assert
    assert normalize_and_validate_pesel(blank_input, allow_blank=True) is None


@pytest.mark.parametrize(
    'blank_input',
    [None, '', '   '],
)
def test_pesel_allow_blank_false_raises(blank_input: str | None) -> None:
    """Sprawdza rzucenie błędu walidacji przy pustym numerze PESEL, gdy allow_blank jest wyłączone."""
    # Act
    with pytest.raises(DjangoValidationError) as exc_info:
        normalize_and_validate_pesel(blank_input, allow_blank=False)
    # Assert
    assert PESEL_REQUIRED in exc_info.value.messages
    assert exc_info.value.code == 'required'


def test_pesel_too_long_raises() -> None:
    """Sprawdza rzucenie błędu walidacji przy zbyt długim numerze PESEL."""
    # Act
    with pytest.raises(DjangoValidationError) as exc_info:
        normalize_and_validate_pesel('9207130425100')
    # Assert
    assert PESEL_TOO_LONG in exc_info.value.messages
    assert exc_info.value.code == 'max_length'


@pytest.mark.parametrize(
    'invalid_format_input',
    [
        '1234567890',   
        '9207130425A',
        '920713-4251',
    ],
)
def test_pesel_invalid_format_raises(invalid_format_input: str) -> None:
    """Sprawdza rzucenie błędu walidacji przy nieprawidłowym formacie znaków w numerze PESEL."""
    # Act
    with pytest.raises(DjangoValidationError) as exc_info:
        normalize_and_validate_pesel(invalid_format_input)
    # Assert
    assert PESEL_INVALID_FORMAT in exc_info.value.messages
    assert exc_info.value.code == 'invalid'


def test_pesel_invalid_date_raises() -> None:
    """Sprawdza rzucenie błędu walidacji przy niepoprawnej dacie zaszyfrowanej w PESEL."""
    # Act
    with pytest.raises(DjangoValidationError) as exc_info:
        normalize_and_validate_pesel('92131304251')
    # Assert
    assert PESEL_INVALID_DATE in exc_info.value.messages
    assert exc_info.value.code == 'invalid_date'


def test_pesel_invalid_checksum_raises() -> None:
    """Sprawdza rzucenie błędu walidacji przy błędnej cyfrze kontrolnej PESEL."""
    # Act
    with pytest.raises(DjangoValidationError) as exc_info:
        normalize_and_validate_pesel('92071304252')
    # Assert
    assert PESEL_INVALID_CHECKSUM in exc_info.value.messages
    assert exc_info.value.code == 'invalid_checksum'


def test_pesel_type_errors() -> None:
    """Sprawdza zgłaszanie wyjątków TypeError dla niepoprawnych typów argumentów w funkcjach PESEL."""
    # Arrange
    from patients.pesel_policy import _has_valid_checksum

    # Act
    with pytest.raises(TypeError, match='Parametr digits musi być ciągiem znaków.'):
        _decode_pesel_birth_date(12345678901)

    with pytest.raises(TypeError, match='Parametr digits musi być ciągiem znaków.'):
        _has_valid_checksum(12345678901)

    with pytest.raises(TypeError, match='Parametr allow_blank musi być wartością logiczną'):
        normalize_and_validate_pesel('92071304259', allow_blank='not_bool')


