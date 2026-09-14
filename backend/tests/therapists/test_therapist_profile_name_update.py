import pytest

from therapists.serializers import TherapistProfileUpdateSerializer


@pytest.mark.django_db
def test_therapist_update_serializer_name_update(therapist):
    serializer = TherapistProfileUpdateSerializer(
        instance=therapist,
        data={
            'first_name': 'Marta',
            'last_name': 'Wiśniewska',
            'phone': '+48 500 600 700',
        },
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    updated_profile = serializer.save()
    assert updated_profile.user.first_name == 'Marta'
    assert updated_profile.user.last_name == 'Wiśniewska'
    assert updated_profile.phone == '+48500600700'


@pytest.mark.django_db
def test_therapist_update_serializer_invalid_last_name(therapist):
    serializer = TherapistProfileUpdateSerializer(
        instance=therapist,
        data={'last_name': '1234'},
        partial=True,
    )
    assert not serializer.is_valid()
    assert 'last_name' in serializer.errors
