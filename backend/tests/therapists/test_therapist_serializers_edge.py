import pytest
from rest_framework.exceptions import ValidationError

from therapists.serializers import TherapistProfileUpdateSerializer


def test_therapist_update_serializer_valid_data():
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
    assert serializer.is_valid(), serializer.errors
    validated = serializer.validated_data
    assert validated['phone'] == '+48123456789'
    assert validated['experience_years'] == 5


@pytest.mark.parametrize(
    'invalid_phone',
    ['123', 'abc', '+4812345678901234567890'],
)
def test_therapist_update_serializer_invalid_phone(invalid_phone):
    serializer = TherapistProfileUpdateSerializer(data={'phone': invalid_phone})
    assert not serializer.is_valid()
    assert 'phone' in serializer.errors


def test_therapist_update_serializer_invalid_experience_years():
    serializer_negative = TherapistProfileUpdateSerializer(data={'experience_years': -1})
    assert not serializer_negative.is_valid()
    assert 'experience_years' in serializer_negative.errors

    serializer_too_high = TherapistProfileUpdateSerializer(data={'experience_years': 61})
    assert not serializer_too_high.is_valid()
    assert 'experience_years' in serializer_too_high.errors


def test_therapist_update_serializer_courses_not_list():
    serializer = TherapistProfileUpdateSerializer(data={'courses': 'not-a-list'})
    assert not serializer.is_valid()
    assert 'courses' in serializer.errors
