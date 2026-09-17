import pytest

from patients.serializers import MeProfileUpdateSerializer


@pytest.mark.django_db
def test_patient_update_serializer_name_and_pesel_update(patient: object) -> None:
    """Sprawdza pomyślną aktualizację imienia, nazwiska oraz numeru telefonu w profilu pacjenta."""
    # Arrange
    serializer: MeProfileUpdateSerializer = MeProfileUpdateSerializer(
        instance=patient,
        data={
            'first_name': 'Janusz',
            'last_name': 'Kowalski-Nowak',
            'phone': '+48 600 700 800',
        },
        partial=True,
    )
    # Assert
    assert serializer.is_valid(), serializer.errors
    updated_profile: object = serializer.save()
    assert updated_profile.user.first_name == 'Janusz'
    assert updated_profile.user.last_name == 'Kowalski-Nowak'
    assert updated_profile.phone == '+48600700800'


@pytest.mark.django_db
def test_patient_update_serializer_invalid_first_name(patient: object) -> None:
    """Sprawdza odrzucenie zbyt krótkiego imienia w profilu pacjenta przez serializator."""
    # Arrange
    serializer: MeProfileUpdateSerializer = MeProfileUpdateSerializer(
        instance=patient,
        data={'first_name': 'A'},
        partial=True,
    )
    # Assert
    assert not serializer.is_valid()
    assert 'first_name' in serializer.errors

