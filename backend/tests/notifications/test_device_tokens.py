import pytest
from rest_framework import status

SAMPLE_TOKEN: str = 'ExponentPushToken[physiocare-test-device]'


@pytest.mark.django_db
def test_patient_registers_and_deletes_device_token(
    api_client: object, patient: object,
) -> None:
    """Sprawdza rejestrację, ponowne przesłanie oraz usunięcie tokena urządzenia push pacjenta."""
    # Arrange
    api_client.force_authenticate(user=patient.user)

    created: object = api_client.post(
        '/api/v1/me/device-tokens/',
        {'expo_push_token': SAMPLE_TOKEN, 'platform': 'android'},
        format='json',
    )
    # Assert
    assert created.status_code == status.HTTP_200_OK
    assert created.data['expo_push_token'] == SAMPLE_TOKEN
    assert created.data['platform'] == 'android'
    assert created.data['is_active'] is True

    listed: object = api_client.get('/api/v1/me/device-tokens/')
    assert listed.status_code == status.HTTP_200_OK
    assert len(listed.data) == 1

    again: object = api_client.post(
        '/api/v1/me/device-tokens/',
        {'expo_push_token': SAMPLE_TOKEN, 'platform': 'android'},
        format='json',
    )
    assert again.status_code == status.HTTP_200_OK
    assert again.data['id'] == created.data['id']

    deleted: object = api_client.delete(
        '/api/v1/me/device-tokens/',
        {'expo_push_token': SAMPLE_TOKEN},
        format='json',
    )
    assert deleted.status_code == status.HTTP_204_NO_CONTENT
    # Act

    listed = api_client.get('/api/v1/me/device-tokens/')
    assert listed.data == []


@pytest.mark.django_db
def test_device_token_rejects_invalid_format(
    api_client: object, patient: object,
) -> None:
    """Sprawdza odrzucenie tokenu urządzenia o niepoprawnym formacie."""
    # Arrange
    api_client.force_authenticate(user=patient.user)
    response: object = api_client.post(
        '/api/v1/me/device-tokens/',
        {'expo_push_token': 'not-a-token'},
        format='json',
    )
    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_therapist_cannot_register_device_token(
    api_client: object, therapist: object,
) -> None:
    """Sprawdza brak możliwości rejestracji tokena urządzenia push przez fizjoterapeutę."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)
    response: object = api_client.post(
        '/api/v1/me/device-tokens/',
        {'expo_push_token': SAMPLE_TOKEN, 'platform': 'ios'},
        format='json',
    )
    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN

