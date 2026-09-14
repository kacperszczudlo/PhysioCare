import pytest
from rest_framework.exceptions import ValidationError

from patients.serializers import MeProfileUpdateSerializer


@pytest.mark.django_db
def test_patient_update_serializer_name_and_pesel_update(patient):
    serializer = MeProfileUpdateSerializer(
        instance=patient,
        data={
            'first_name': 'Janusz',
            'last_name': 'Kowalski-Nowak',
            'phone': '+48 600 700 800',
        },
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    updated_profile = serializer.save()
    assert updated_profile.user.first_name == 'Janusz'
    assert updated_profile.user.last_name == 'Kowalski-Nowak'
    assert updated_profile.phone == '+48600700800'


@pytest.mark.django_db
def test_patient_update_serializer_invalid_first_name(patient):
    serializer = MeProfileUpdateSerializer(
        instance=patient,
        data={'first_name': 'A'},
        partial=True,
    )
    assert not serializer.is_valid()
    assert 'first_name' in serializer.errors
