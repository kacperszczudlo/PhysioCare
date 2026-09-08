import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.serializers import PatientRegistrationSerializer
from notifications.keys import CANONICAL_PREF_KEYS
from notifications.models import NotificationPreference


def _patient_auth(api_client, patient):
    token = str(RefreshToken.for_user(patient.user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')


def _pref_map(payload):
    return {item['pref_key']: item['enabled'] for item in payload}


@pytest.mark.django_db
def test_get_seeds_canonical_preferences_enabled(api_client, patient):
    _patient_auth(api_client, patient)

    response = api_client.get('/api/v1/me/notification-preferences/')

    assert response.status_code == status.HTTP_200_OK
    assert [item['pref_key'] for item in response.data] == list(CANONICAL_PREF_KEYS)
    assert all(item['enabled'] is True for item in response.data)
    assert NotificationPreference.objects.filter(user=patient.user).count() == len(
        CANONICAL_PREF_KEYS
    )


@pytest.mark.django_db
def test_patch_updates_known_key(api_client, patient):
    _patient_auth(api_client, patient)

    response = api_client.patch(
        '/api/v1/me/notification-preferences/',
        {'visit_reminder': False},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    prefs = _pref_map(response.data)
    assert prefs['visit_reminder'] is False
    assert prefs['visit_change'] is True
    assert set(prefs) == set(CANONICAL_PREF_KEYS)


@pytest.mark.django_db
def test_patch_accepts_preferences_wrapper(api_client, patient):
    _patient_auth(api_client, patient)

    response = api_client.patch(
        '/api/v1/me/notification-preferences/',
        {'preferences': {'waitlist': False, 'new_document': False}},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    prefs = _pref_map(response.data)
    assert prefs['waitlist'] is False
    assert prefs['new_document'] is False
    assert prefs['exercise_reminder'] is True


@pytest.mark.django_db
def test_patch_rejects_unknown_keys(api_client, patient):
    _patient_auth(api_client, patient)

    response = api_client.patch(
        '/api/v1/me/notification-preferences/',
        {'visit_reminders': True, 'visit_reminder': False},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert NotificationPreference.objects.filter(
        user=patient.user,
        pref_key='visit_reminders',
    ).exists() is False
    assert NotificationPreference.objects.filter(
        user=patient.user,
        pref_key='visit_reminder',
        enabled=False,
    ).exists() is False


@pytest.mark.django_db
def test_therapist_cannot_access_notification_preferences(api_client, therapist):
    api_client.force_authenticate(user=therapist.user)

    response = api_client.get('/api/v1/me/notification-preferences/')

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_patient_registration_seeds_notification_preferences(therapist):
    serializer = PatientRegistrationSerializer(
        data={
            'email': 'nowy.pacjent@physiocare.test',
            'password': 'SecurePass123!',
            'first_name': 'Jan',
            'last_name': 'Kowalski',
            'therapist_id': str(therapist.id),
            'consents': {'terms': True, 'medical_data': True},
        }
    )
    assert serializer.is_valid(), serializer.errors
    user = serializer.save()

    keys = set(
        NotificationPreference.objects.filter(user=user).values_list(
            'pref_key',
            flat=True,
        )
    )
    assert keys == set(CANONICAL_PREF_KEYS)
    assert not NotificationPreference.objects.filter(
        user=user,
        enabled=False,
    ).exists()
