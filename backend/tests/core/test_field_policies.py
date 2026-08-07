import pytest
from django.core.exceptions import ValidationError

from core.field_policies import (
    normalize_and_validate_first_name,
    normalize_and_validate_icd10,
    normalize_and_validate_last_name,
)
from core.phone_policy import PHONE_INVALID, normalize_and_validate_phone
from patients.pesel_policy import (
    PESEL_INVALID_CHECKSUM,
    PESEL_INVALID_FORMAT,
    normalize_and_validate_pesel,
)
from patients.serializers import MeProfileUpdateSerializer
from therapists.pwzf_policy import PWZF_INVALID, normalize_and_validate_pwzf
from accounts.serializers import TherapistRegistrationSerializer


VALID_PESEL = '44051401359'


def test_pesel_accepts_valid_number():
    assert normalize_and_validate_pesel(VALID_PESEL) == VALID_PESEL


def test_pesel_rejects_wrong_checksum():
    with pytest.raises(ValidationError) as exc:
        normalize_and_validate_pesel('44051401358')
    assert PESEL_INVALID_CHECKSUM in exc.value.messages


def test_pesel_rejects_non_digits():
    with pytest.raises(ValidationError) as exc:
        normalize_and_validate_pesel('4405140135A')
    assert PESEL_INVALID_FORMAT in exc.value.messages


def test_pesel_allows_blank():
    assert normalize_and_validate_pesel('') is None
    assert normalize_and_validate_pesel(None) is None


def test_phone_normalizes_polish_formats():
    assert normalize_and_validate_phone('512 345 678') == '+48512345678'
    assert normalize_and_validate_phone('+48 512-345-678') == '+48512345678'
    assert normalize_and_validate_phone('0512345678') == '+48512345678'


def test_phone_rejects_invalid():
    with pytest.raises(ValidationError) as exc:
        normalize_and_validate_phone('12345')
    assert PHONE_INVALID in exc.value.messages


def test_phone_allows_blank():
    assert normalize_and_validate_phone('') == ''
    assert normalize_and_validate_phone(None) == ''


def test_pwzf_accepts_digit_license():
    assert normalize_and_validate_pwzf('12345') == '12345'
    assert normalize_and_validate_pwzf('12-345') == '12345'
    assert normalize_and_validate_pwzf('PWZFz nr 12345') == '12345'


def test_pwzf_rejects_wrong_length():
    with pytest.raises(ValidationError) as exc:
        normalize_and_validate_pwzf('001')
    assert PWZF_INVALID in exc.value.messages


def test_pwzf_rejects_letters():
    with pytest.raises(ValidationError) as exc:
        normalize_and_validate_pwzf('PWZF-ABCD')
    assert PWZF_INVALID in exc.value.messages


def test_names_reject_digits():
    with pytest.raises(ValidationError):
        normalize_and_validate_first_name('Jan3')
    with pytest.raises(ValidationError):
        normalize_and_validate_last_name('Kowal5ki')


def test_icd10_accepts_standard_codes():
    assert normalize_and_validate_icd10('m54.5') == 'M54.5'
    assert normalize_and_validate_icd10('') == ''


def test_icd10_rejects_garbage():
    with pytest.raises(ValidationError):
        normalize_and_validate_icd10('XYZ')


@pytest.mark.django_db
def test_patient_profile_update_rejects_invalid_pesel_and_phone():
    serializer = MeProfileUpdateSerializer(
        data={'pesel': '12345678901', 'phone': 'abc'},
    )
    assert not serializer.is_valid()
    assert 'pesel' in serializer.errors
    assert 'phone' in serializer.errors


@pytest.mark.django_db
def test_therapist_register_rejects_invalid_pwzf():
    serializer = TherapistRegistrationSerializer(
        data={
            'email': 'pwzf.ok@physiocare.test',
            'password': 'SecurePass123!',
            'first_name': 'Anna',
            'last_name': 'Nowak',
            'pwzf_number': 'AB',
            'pwzf_declaration': True,
        }
    )
    assert not serializer.is_valid()
    assert 'pwzf_number' in serializer.errors
    assert PWZF_INVALID in str(serializer.errors['pwzf_number'])


@pytest.mark.django_db
def test_therapist_register_accepts_digit_pwzf():
    serializer = TherapistRegistrationSerializer(
        data={
            'email': 'pwzf.valid@physiocare.test',
            'password': 'SecurePass123!',
            'first_name': 'Anna',
            'last_name': 'Nowak',
            'pwzf_number': '64127',
            'pwzf_declaration': True,
        }
    )
    assert serializer.is_valid(), serializer.errors
