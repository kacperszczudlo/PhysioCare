import pytest

from accounts.password_policy import (
    PASSWORD_ENTIRELY_NUMERIC,
    PASSWORD_NO_SPECIAL,
    PASSWORD_TOO_COMMON,
    PASSWORD_TOO_SHORT,
)
from accounts.serializers import TherapistRegistrationSerializer


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('password', 'expected_fragment'),
    [
        ('short', PASSWORD_TOO_SHORT),
        ('12345678', PASSWORD_ENTIRELY_NUMERIC),
        ('password', PASSWORD_TOO_COMMON),
        ('SecurePass123', PASSWORD_NO_SPECIAL),
    ],
)
def test_therapist_register_rejects_weak_password(password: str, expected_fragment: str) -> None:
    """Sprawdza, czy rejestracja fizjoterapeuty odrzuca słabe hasła z odpowiednim komunikatem."""
    # Arrange
    serializer = TherapistRegistrationSerializer(
        data={
            'email': 'new.therapist@physiocare.test',
            'password': password,
            'first_name': 'Anna',
            'last_name': 'Kowalska',
            'pwzf_number': '81001',
            'pwzf_declaration': True,
        }
    )

    # Assert
    assert not serializer.is_valid()
    assert 'password' in serializer.errors
    assert expected_fragment in str(serializer.errors['password'])


@pytest.mark.django_db
def test_therapist_register_rejects_password_similar_to_email() -> None:
    """Sprawdza, czy rejestracja odrzuca hasło zbyt podobne do adresu e-mail."""
    # Arrange
    serializer = TherapistRegistrationSerializer(
        data={
            'email': 'jan.nowak@physiocare.test',
            'password': 'jan.nowak',
            'first_name': 'Jan',
            'last_name': 'Nowak',
            'pwzf_number': '81002',
            'pwzf_declaration': True,
        }
    )

    # Assert
    assert not serializer.is_valid()
    assert 'password' in serializer.errors
    assert 'podobne' in str(serializer.errors['password']).lower()


@pytest.mark.django_db
def test_therapist_register_accepts_strong_password() -> None:
    """Sprawdza, czy rejestracja akceptuje silne, spełniające kryteria polityki hasło."""
    # Arrange
    serializer = TherapistRegistrationSerializer(
        data={
            'email': 'strong.therapist@physiocare.test',
            'password': 'SecurePass123!',
            'first_name': 'Ewa',
            'last_name': 'Lis',
            'pwzf_number': '81003',
            'pwzf_declaration': True,
        }
    )

    # Assert
    assert serializer.is_valid(), serializer.errors
    user = serializer.save()
    assert user.check_password('SecurePass123!')

