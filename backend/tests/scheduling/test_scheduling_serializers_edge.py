import pytest
from django.utils import timezone

from scheduling.serializers import TherapyTypeSerializer, VisitSerializer


def test_therapy_type_serializer_valid_data():
    serializer = TherapyTypeSerializer(
        data={
            'name': 'Fizjoterapia ortopedyczna',
            'color_hex': '#10b981',
            'duration_min': 45,
        }
    )
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data['name'] == 'Fizjoterapia ortopedyczna'
    assert serializer.validated_data['color_hex'] == '#10B981'
    assert serializer.validated_data['duration_min'] == 45


@pytest.mark.parametrize(
    'invalid_color',
    ['#12345', 'blue', '10b981', '#1234567'],
)
def test_therapy_type_serializer_invalid_color_hex(invalid_color):
    serializer = TherapyTypeSerializer(
        data={
            'name': 'Masaż',
            'color_hex': invalid_color,
            'duration_min': 30,
        }
    )
    assert not serializer.is_valid()
    assert 'color_hex' in serializer.errors


@pytest.mark.parametrize('invalid_duration', [0, 4, 481, -15])
def test_therapy_type_serializer_invalid_duration(invalid_duration):
    serializer = TherapyTypeSerializer(
        data={
            'name': 'Masaż',
            'color_hex': '#3b82f6',
            'duration_min': invalid_duration,
        }
    )
    assert not serializer.is_valid()
    assert 'duration_min' in serializer.errors


def test_visit_serializer_end_before_start_raises():
    now = timezone.now()
    serializer = VisitSerializer(
        data={
            'start_at': now.isoformat(),
            'end_at': (now - timezone.timedelta(minutes=15)).isoformat(),
        }
    )
    assert not serializer.is_valid()
    assert 'end_at' in serializer.errors
