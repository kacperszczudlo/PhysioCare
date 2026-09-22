import pytest
from django.core.exceptions import ValidationError as DjangoValidationError

from therapists.pwzf_policy import (
    PWZF_INVALID,
    PWZF_REQUIRED,
    PWZF_TOO_LONG,
    normalize_and_validate_pwzf,
)


@pytest.mark.parametrize(
    'input_value,expected_output',
    [
        ('12345', '12345'),
        ('  12345  ', '12345'),
        ('PWZFz nr 12345', '12345'),
        ('pwzf: 12345', '12345'),
        ('PWZF-12345', '12345'),
        ('PWZFz 12 345', '12345'),
    ],
)
def test_normalize_and_validate_pwzf_valid(input_value: str, expected_output: str) -> None:
    """Sprawdza poprawną normalizację prawidłowych numerów PWZFz."""
    # Assert
    assert normalize_and_validate_pwzf(input_value) == expected_output


@pytest.mark.parametrize('blank_val', [None, '', '   '])
def test_normalize_and_validate_pwzf_blank_raises(blank_val: str | None) -> None:
    """Sprawdza rzucenie błędu walidacji przy braku lub pustym numerze PWZFz."""
    # Act
    with pytest.raises(DjangoValidationError) as exc_info:
        normalize_and_validate_pwzf(blank_val)
    # Assert
    assert PWZF_REQUIRED in exc_info.value.messages
    assert exc_info.value.code == 'required'


def test_normalize_and_validate_pwzf_too_long_raises() -> None:
    """Sprawdza rzucenie błędu walidacji przy zbyt długim numerze PWZFz."""
    # Arrange
    long_input: str = 'PWZFz nr ' + '1' * 25
    # Act
    with pytest.raises(DjangoValidationError) as exc_info:
        normalize_and_validate_pwzf(long_input)
    # Assert
    assert PWZF_TOO_LONG in exc_info.value.messages
    assert exc_info.value.code == 'max_length'


@pytest.mark.parametrize(
    'invalid_val',
    [
        '1234',
        '123456',
        'ABCDE',
        'PWZFz 123A5',
    ],
)
def test_normalize_and_validate_pwzf_invalid_raises(invalid_val: str) -> None:
    """Sprawdza rzucenie błędu walidacji przy niepoprawnym formacie cyfr PWZFz."""
    # Act
    with pytest.raises(DjangoValidationError) as exc_info:
        normalize_and_validate_pwzf(invalid_val)
    # Assert
    assert PWZF_INVALID in exc_info.value.messages
    assert exc_info.value.code == 'invalid'

