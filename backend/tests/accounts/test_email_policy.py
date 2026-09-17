import pytest

from accounts.email_policy import EMAIL_INVALID, EMAIL_REQUIRED, EMAIL_TAKEN
from accounts.serializers import (
    PasswordResetRequestSerializer,
    PatientRegistrationSerializer,
    TherapistRegistrationSerializer,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'email',
    [
        'not-an-email',
        'a@',
        '@example.com',
        'jan example.com',
    ],
)
def test_patient_register_rejects_invalid_email_with_polish_message(email: str, therapist: object) -> None:
    """Sprawdza, czy rejestracja pacjenta odrzuca niepoprawny e-mail polskim komunikatem."""
    # Arrange
    serializer = PatientRegistrationSerializer(
        data={
            'email': email,
            'password': 'SecurePass123!',
            'first_name': 'Jan',
            'last_name': 'Kowalski',
            'therapist_id': str(therapist.id),
            'consents': {'terms': True, 'medical_data': True},
        }
    )

    # Assert
    assert not serializer.is_valid()
    assert 'email' in serializer.errors
    assert EMAIL_INVALID in str(serializer.errors['email'])
    assert 'Ensure this field' not in str(serializer.errors)
    assert 'Enter a valid email' not in str(serializer.errors)


@pytest.mark.django_db
def test_patient_register_rejects_blank_email(therapist: object) -> None:
    """Sprawdza, czy rejestracja pacjenta odrzuca pusty e-mail."""
    # Arrange
    serializer = PatientRegistrationSerializer(
        data={
            'email': '',
            'password': 'SecurePass123!',
            'first_name': 'Jan',
            'last_name': 'Kowalski',
            'therapist_id': str(therapist.id),
            'consents': {'terms': True, 'medical_data': True},
        }
    )

    # Assert
    assert not serializer.is_valid()
    assert EMAIL_REQUIRED in str(serializer.errors['email'])


@pytest.mark.django_db
def test_patient_register_rejects_taken_email(patient: object, therapist: object) -> None:
    """Sprawdza, czy rejestracja pacjenta odrzuca już zajęty e-mail."""
    # Arrange
    serializer = PatientRegistrationSerializer(
        data={
            'email': patient.user.email,
            'password': 'SecurePass123!',
            'first_name': 'Jan',
            'last_name': 'Kowalski',
            'therapist_id': str(therapist.id),
            'consents': {'terms': True, 'medical_data': True},
        }
    )

    # Assert
    assert not serializer.is_valid()
    assert EMAIL_TAKEN in str(serializer.errors['email'])


@pytest.mark.django_db
def test_therapist_register_rejects_invalid_email() -> None:
    """Sprawdza, czy rejestracja fizjoterapeuty odrzuca niepoprawny e-mail."""
    # Arrange
    serializer = TherapistRegistrationSerializer(
        data={
            'email': 'zly-email',
            'password': 'SecurePass123!',
            'first_name': 'Anna',
            'last_name': 'Nowak',
            'pwzf_number': '82001',
            'pwzf_declaration': True,
        }
    )

    # Assert
    assert not serializer.is_valid()
    assert EMAIL_INVALID in str(serializer.errors['email'])


def test_password_reset_request_rejects_invalid_email() -> None:
    """Sprawdza, czy wniosek o reset hasła odrzuca niepoprawny e-mail."""
    # Arrange
    serializer = PasswordResetRequestSerializer(data={'email': 'niepoprawny'})
    # Assert
    assert not serializer.is_valid()
    assert EMAIL_INVALID in str(serializer.errors['email'])


@pytest.mark.django_db
def test_therapist_register_pwzf_format_is_polish() -> None:
    """Sprawdza, czy błąd formatu numeru PWZF jest w języku polskim."""
    # Arrange
    serializer = TherapistRegistrationSerializer(
        data={
            'email': 'ok.therapist@physiocare.test',
            'password': 'SecurePass123!',
            'first_name': 'Anna',
            'last_name': 'Nowak',
            'pwzf_number': '12',
            'pwzf_declaration': True,
        }
    )

    # Assert
    assert not serializer.is_valid()
    assert 'pwzf_number' in serializer.errors
    message = str(serializer.errors['pwzf_number'])
    assert '5' in message
    assert 'Ensure this field' not in message

