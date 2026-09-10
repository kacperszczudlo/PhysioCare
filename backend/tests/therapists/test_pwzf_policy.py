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
def test_normalize_and_validate_pwzf_valid(input_value, expected_output):
    assert normalize_and_validate_pwzf(input_value) == expected_output


@pytest.mark.parametrize('blank_val', [None, '', '   '])
def test_normalize_and_validate_pwzf_blank_raises(blank_val):
    with pytest.raises(DjangoValidationError) as exc_info:
        normalize_and_validate_pwzf(blank_val)
    assert PWZF_REQUIRED in exc_info.value.messages
    assert exc_info.value.code == 'required'


def test_normalize_and_validate_pwzf_too_long_raises():
    long_input = 'PWZFz nr ' + '1' * 25
    with pytest.raises(DjangoValidationError) as exc_info:
        normalize_and_validate_pwzf(long_input)
    assert PWZF_TOO_LONG in exc_info.value.messages
    assert exc_info.value.code == 'max_length'


@pytest.mark.parametrize(
    'invalid_val',
    [
        '1234',       # 4 digits
        '123456',     # 6 digits
        'ABCDE',      # letters without prefix
        'PWZFz 123A5',# contains letter in digits
    ],
)
def test_normalize_and_validate_pwzf_invalid_raises(invalid_val):
    with pytest.raises(DjangoValidationError) as exc_info:
        normalize_and_validate_pwzf(invalid_val)
    assert PWZF_INVALID in exc_info.value.messages
    assert exc_info.value.code == 'invalid'
