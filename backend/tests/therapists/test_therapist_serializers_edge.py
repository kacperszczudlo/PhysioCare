import pytest

from therapists.serializers import TherapistProfileUpdateSerializer


def test_therapist_update_serializer_valid_data() -> None:
    """Sprawdza pomyślną walidację poprawnych danych profilu fizjoterapeuty."""
    # Arrange
    serializer = TherapistProfileUpdateSerializer(
        data={
            'phone': '+48 123 456 789',
            'location_address': 'ul. Medyczna 10, Warszawa',
            'bio': 'Doświadczony fizjoterapeuta specjalizujący się w kinezjoterapii.',
            'courses': ['PNF podstawowy', 'Kinesiotaping'],
            'qualification_level': 'MAGISTER',
            'experience_years': 5,
        }
    )
    # Assert
    assert serializer.is_valid(), serializer.errors
    validated = serializer.validated_data
    assert validated['phone'] == '+48123456789'
    assert validated['experience_years'] == 5


@pytest.mark.parametrize(
    'invalid_phone',
    ['123', 'abc', '+4812345678901234567890'],
)
def test_therapist_update_serializer_invalid_phone(invalid_phone: str) -> None:
    """Sprawdza odrzucenie błędnych formatów numeru telefonu."""
    # Arrange
    serializer = TherapistProfileUpdateSerializer(data={'phone': invalid_phone})
    # Assert
    assert not serializer.is_valid()
    assert 'phone' in serializer.errors


def test_therapist_update_serializer_invalid_experience_years() -> None:
    """Sprawdza walidację zakresem lat doświadczenia (ujemne lub ponad 60)."""
    # Arrange
    serializer_negative = TherapistProfileUpdateSerializer(data={'experience_years': -1})
    # Assert
    assert not serializer_negative.is_valid()
    assert 'experience_years' in serializer_negative.errors

    serializer_too_high = TherapistProfileUpdateSerializer(data={'experience_years': 61})
    assert not serializer_too_high.is_valid()
    assert 'experience_years' in serializer_too_high.errors


def test_therapist_update_serializer_courses_not_list() -> None:
    """Sprawdza odrzucenie wartości pola kursy, jeśli nie jest listą."""
    # Arrange
    serializer = TherapistProfileUpdateSerializer(data={'courses': 'not-a-list'})
    # Assert
    assert not serializer.is_valid()
    assert 'courses' in serializer.errors

