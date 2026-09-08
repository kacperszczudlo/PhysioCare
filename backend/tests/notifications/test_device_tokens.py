import pytest
from rest_framework import status

SAMPLE_TOKEN = 'ExponentPushToken[physiocare-test-device]'


@pytest.mark.django_db
def test_patient_registers_and_deletes_device_token(api_client, patient):
    api_client.force_authenticate(user=patient.user)

    created = api_client.post(
        '/api/v1/me/device-tokens/',
        {'expo_push_token': SAMPLE_TOKEN, 'platform': 'android'},
        format='json',
    )
    assert created.status_code == status.HTTP_200_OK
    assert created.data['expo_push_token'] == SAMPLE_TOKEN
    assert created.data['platform'] == 'android'
    assert created.data['is_active'] is True

    listed = api_client.get('/api/v1/me/device-tokens/')
    assert listed.status_code == status.HTTP_200_OK
    assert len(listed.data) == 1

    again = api_client.post(
        '/api/v1/me/device-tokens/',
        {'expo_push_token': SAMPLE_TOKEN, 'platform': 'android'},
        format='json',
    )
    assert again.status_code == status.HTTP_200_OK
    assert again.data['id'] == created.data['id']

    deleted = api_client.delete(
        '/api/v1/me/device-tokens/',
        {'expo_push_token': SAMPLE_TOKEN},
        format='json',
    )
    assert deleted.status_code == status.HTTP_204_NO_CONTENT

    listed = api_client.get('/api/v1/me/device-tokens/')
    assert listed.data == []


@pytest.mark.django_db
def test_device_token_rejects_invalid_format(api_client, patient):
    api_client.force_authenticate(user=patient.user)
    response = api_client.post(
        '/api/v1/me/device-tokens/',
        {'expo_push_token': 'not-a-token'},
        format='json',
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_therapist_cannot_register_device_token(api_client, therapist):
    api_client.force_authenticate(user=therapist.user)
    response = api_client.post(
        '/api/v1/me/device-tokens/',
        {'expo_push_token': SAMPLE_TOKEN, 'platform': 'ios'},
        format='json',
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
