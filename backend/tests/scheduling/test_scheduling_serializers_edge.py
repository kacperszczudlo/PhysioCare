import pytest
from django.utils import timezone

from scheduling.serializers import TherapyTypeSerializer, VisitSerializer


def test_therapy_type_serializer_valid_data() -> None:
    """Sprawdza pomyślną walidację poprawnych danych typu terapii."""
    # Arrange
    serializer = TherapyTypeSerializer(
        data={
            'name': 'Fizjoterapia ortopedyczna',
            'color_hex': '#10b981',
            'duration_min': 45,
        }
    )
    # Assert
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data['name'] == 'Fizjoterapia ortopedyczna'
    assert serializer.validated_data['color_hex'] == '#10B981'
    assert serializer.validated_data['duration_min'] == 45


@pytest.mark.parametrize(
    'invalid_color',
    ['#12345', 'blue', '10b981', '#1234567'],
)
def test_therapy_type_serializer_invalid_color_hex(invalid_color: str) -> None:
    """Sprawdza odrzucenie niepoprawnych kodów szesnastkowych koloru."""
    # Arrange
    serializer = TherapyTypeSerializer(
        data={
            'name': 'Masaż',
            'color_hex': invalid_color,
            'duration_min': 30,
        }
    )
    # Assert
    assert not serializer.is_valid()
    assert 'color_hex' in serializer.errors


@pytest.mark.parametrize('invalid_duration', [0, 4, 481, -15])
def test_therapy_type_serializer_invalid_duration(invalid_duration: int) -> None:
    """Sprawdza odrzucenie nieprawidłowych czasów trwania zabiegu."""
    # Arrange
    serializer = TherapyTypeSerializer(
        data={
            'name': 'Masaż',
            'color_hex': '#3b82f6',
            'duration_min': invalid_duration,
        }
    )
    # Assert
    assert not serializer.is_valid()
    assert 'duration_min' in serializer.errors


def test_visit_serializer_end_before_start_raises() -> None:
    """Sprawdza błąd walidacji, gdy czas zakończenia wizyty jest przed czasem rozpoczęcia."""
    # Arrange
    now = timezone.now()
    serializer = VisitSerializer(
        data={
            'start_at': now.isoformat(),
            'end_at': (now - timezone.timedelta(minutes=15)).isoformat(),
        }
    )
    # Assert
    assert not serializer.is_valid()
    assert 'end_at' in serializer.errors

