import pytest
from django.core.exceptions import ValidationError

from accounts.serializers import TherapistRegistrationSerializer
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

VALID_PESEL: str = '44051401359'


def test_pesel_accepts_valid_number() -> None:
    """Sprawdza akceptację poprawnego numeru PESEL."""
    # Assert
    assert normalize_and_validate_pesel(VALID_PESEL) == VALID_PESEL


def test_pesel_rejects_wrong_checksum() -> None:
    """Sprawdza odrzucenie numeru PESEL z błędną cyfrą kontrolną."""
    # Act
    with pytest.raises(ValidationError) as exc:
        normalize_and_validate_pesel('44051401358')
    # Assert
    assert PESEL_INVALID_CHECKSUM in exc.value.messages


def test_pesel_rejects_non_digits() -> None:
    """Sprawdza odrzucenie numeru PESEL zawierającego znaki inne niż cyfry."""
    # Act
    with pytest.raises(ValidationError) as exc:
        normalize_and_validate_pesel('4405140135A')
    # Assert
    assert PESEL_INVALID_FORMAT in exc.value.messages


def test_pesel_allows_blank() -> None:
    """Sprawdza zezwalanie na pusty numer PESEL (pusty ciąg lub None)."""
    # Assert
    assert normalize_and_validate_pesel('') is None
    assert normalize_and_validate_pesel(None) is None


def test_phone_normalizes_polish_formats() -> None:
    """Sprawdza normalizację polskich formatów numeru telefonu do formatu E.164."""
    # Assert
    assert normalize_and_validate_phone('512 345 678') == '+48512345678'
    assert normalize_and_validate_phone('+48 512-345-678') == '+48512345678'
    assert normalize_and_validate_phone('0512345678') == '+48512345678'


def test_phone_normalizes_international() -> None:
    """Sprawdza normalizację międzynarodowych numerów telefonu do formatu E.164."""
    # Assert
    assert normalize_and_validate_phone('+49 151 23456789') == '+4915123456789'
    assert normalize_and_validate_phone('+1 202 555 0123') == '+12025550123'


def test_phone_rejects_invalid() -> None:
    """Sprawdza odrzucenie niepoprawnego numeru telefonu."""
    # Act
    with pytest.raises(ValidationError) as exc:
        normalize_and_validate_phone('12345')
    # Assert
    assert PHONE_INVALID in exc.value.messages


def test_phone_allows_blank() -> None:
    """Sprawdza zezwalanie na pusty numer telefonu."""
    # Assert
    assert normalize_and_validate_phone('') == ''
    assert normalize_and_validate_phone(None) == ''


def test_pwzf_accepts_digit_license() -> None:
    """Sprawdza akceptację i normalizację poprawnego numeru PWZFz."""
    # Assert
    assert normalize_and_validate_pwzf('12345') == '12345'
    assert normalize_and_validate_pwzf('12-345') == '12345'
    assert normalize_and_validate_pwzf('PWZFz nr 12345') == '12345'


def test_pwzf_rejects_wrong_length() -> None:
    """Sprawdza odrzucenie numeru PWZFz o niepoprawnej długości."""
    # Act
    with pytest.raises(ValidationError) as exc:
        normalize_and_validate_pwzf('001')
    # Assert
    assert PWZF_INVALID in exc.value.messages


def test_pwzf_rejects_letters() -> None:
    """Sprawdza odrzucenie niepoprawnych liter w numerze PWZFz."""
    # Act
    with pytest.raises(ValidationError) as exc:
        normalize_and_validate_pwzf('PWZF-ABCD')
    # Assert
    assert PWZF_INVALID in exc.value.messages


def test_names_reject_digits() -> None:
    """Sprawdza odrzucenie cyfr w imionach i nazwiskach."""
    # Act
    with pytest.raises(ValidationError):
        normalize_and_validate_first_name('Jan3')
    with pytest.raises(ValidationError):
        normalize_and_validate_last_name('Kowal5ki')


def test_icd10_accepts_standard_codes() -> None:
    """Sprawdza akceptację i normalizację standardowych kodów ICD-10."""
    # Assert
    assert normalize_and_validate_icd10('m54.5') == 'M54.5'
    assert normalize_and_validate_icd10('') == ''


def test_icd10_rejects_garbage() -> None:
    """Sprawdza odrzucenie niepoprawnych kodów ICD-10."""
    # Act
    with pytest.raises(ValidationError):
        normalize_and_validate_icd10('XYZ')


@pytest.mark.django_db
def test_patient_profile_update_rejects_invalid_pesel_and_phone() -> None:
    """Sprawdza odrzucenie niepoprawnego PESEL i telefonu w serializatorze profilu pacjenta."""
    # Arrange
    serializer: MeProfileUpdateSerializer = MeProfileUpdateSerializer(
        data={'pesel': '12345678901', 'phone': 'abc'},
    )
    # Assert
    assert not serializer.is_valid()
    assert 'pesel' in serializer.errors
    assert 'phone' in serializer.errors


@pytest.mark.django_db
def test_therapist_register_rejects_invalid_pwzf() -> None:
    """Sprawdza odrzucenie niepoprawnego numeru PWZFz w rejestracji fizjoterapeuty."""
    # Arrange
    serializer: TherapistRegistrationSerializer = TherapistRegistrationSerializer(
        data={
            'email': 'pwzf.ok@physiocare.test',
            'password': 'SecurePass123!',
            'first_name': 'Anna',
            'last_name': 'Nowak',
            'pwzf_number': 'AB',
            'pwzf_declaration': True,
        }
    )
    # Assert
    assert not serializer.is_valid()
    assert 'pwzf_number' in serializer.errors
    assert PWZF_INVALID in str(serializer.errors['pwzf_number'])


@pytest.mark.django_db
def test_therapist_register_accepts_digit_pwzf() -> None:
    """Sprawdza akceptację poprawnego cyfrowego numeru PWZFz w rejestracji fizjoterapeuty."""
    # Arrange
    serializer: TherapistRegistrationSerializer = TherapistRegistrationSerializer(
        data={
            'email': 'pwzf.valid@physiocare.test',
            'password': 'SecurePass123!',
            'first_name': 'Anna',
            'last_name': 'Nowak',
            'pwzf_number': '64127',
            'pwzf_declaration': True,
        }
    )
    # Assert
    assert serializer.is_valid(), serializer.errors

