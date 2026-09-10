from datetime import date

from django.core.exceptions import ValidationError as DjangoValidationError
import pytest

from patients.pesel_policy import (
    PESEL_INVALID_CHECKSUM,
    PESEL_INVALID_DATE,
    PESEL_INVALID_FORMAT,
    PESEL_REQUIRED,
    PESEL_TOO_LONG,
    _decode_pesel_birth_date,
    _has_valid_checksum,
    normalize_and_validate_pesel,
)


@pytest.mark.parametrize(
    'pesel,expected_date',
    [
        # 1900s: 920713... -> 1992-07-13
        ('92071304259', date(1992, 7, 13)),
        # 2000s: 022715... -> 2002-07-15 (month 27 = 07 + 20)
        ('02271501248', date(2002, 7, 15)),
        # 1800s: 808115... -> 1880-01-15 (month 81 = 01 + 80)
        ('80811501235', date(1880, 1, 15)),
        # 2100s: 154512... -> 2115-05-12 (month 45 = 05 + 40)
        ('15451201234', date(2115, 5, 12)),
        # 2200s: 306520... -> 2230-05-20 (month 65 = 05 + 60)
        ('30652001232', date(2230, 5, 20)),
    ],
)
def test_decode_pesel_birth_date_valid(pesel, expected_date):
    # Act & Assert
    assert _decode_pesel_birth_date(pesel) == expected_date


def test_decode_pesel_birth_date_invalid_month():
    # Month 13 is invalid encoding
    assert _decode_pesel_birth_date('92131304251') is None


def test_decode_pesel_birth_date_invalid_day():
    # Feb 31st (month 02, day 31) is invalid date
    assert _decode_pesel_birth_date('92023104251') is None


@pytest.mark.parametrize(
    'valid_pesel',
    [
        '92071304259',
        '02271501248',
    ],
)
def test_valid_pesel_normalization(valid_pesel):
    # Act & Assert
    assert normalize_and_validate_pesel(valid_pesel) == valid_pesel
    assert normalize_and_validate_pesel(f'  {valid_pesel}  ') == valid_pesel


@pytest.mark.parametrize(
    'blank_input',
    [None, '', '   '],
)
def test_pesel_allow_blank_true(blank_input):
    assert normalize_and_validate_pesel(blank_input, allow_blank=True) is None


@pytest.mark.parametrize(
    'blank_input',
    [None, '', '   '],
)
def test_pesel_allow_blank_false_raises(blank_input):
    with pytest.raises(DjangoValidationError) as exc_info:
        normalize_and_validate_pesel(blank_input, allow_blank=False)
    assert PESEL_REQUIRED in exc_info.value.messages
    assert exc_info.value.code == 'required'


def test_pesel_too_long_raises():
    with pytest.raises(DjangoValidationError) as exc_info:
        normalize_and_validate_pesel('9207130425100')
    assert PESEL_TOO_LONG in exc_info.value.messages
    assert exc_info.value.code == 'max_length'


@pytest.mark.parametrize(
    'invalid_format_input',
    [
        '1234567890',     # 10 digits
        '9207130425A',    # letters
        '920713-4251',    # hyphen
    ],
)
def test_pesel_invalid_format_raises(invalid_format_input):
    with pytest.raises(DjangoValidationError) as exc_info:
        normalize_and_validate_pesel(invalid_format_input)
    assert PESEL_INVALID_FORMAT in exc_info.value.messages
    assert exc_info.value.code == 'invalid'


def test_pesel_invalid_date_raises():
    with pytest.raises(DjangoValidationError) as exc_info:
        normalize_and_validate_pesel('92131304251')
    assert PESEL_INVALID_DATE in exc_info.value.messages
    assert exc_info.value.code == 'invalid_date'


def test_pesel_invalid_checksum_raises():
    # 92071304252 has wrong control digit (should be 1)
    with pytest.raises(DjangoValidationError) as exc_info:
        normalize_and_validate_pesel('92071304252')
    assert PESEL_INVALID_CHECKSUM in exc_info.value.messages
    assert exc_info.value.code == 'invalid_checksum'
