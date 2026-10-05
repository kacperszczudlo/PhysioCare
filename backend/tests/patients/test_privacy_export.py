from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from notifications.defaults import ensure_default_preferences
from notifications.keys import NotificationPreferenceKey
from notifications.models import DeviceToken, NotificationPreference
from scheduling.models import Visit, VisitStatus

if TYPE_CHECKING:
    from rest_framework.test import APIClient

    from patients.models import PatientProfile
    from scheduling.models import TherapyType
    from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_data_export_includes_clinical_collections(
    api_client: 'APIClient',
    patient: 'PatientProfile',
    therapist: 'TherapistProfile',
    therapy_type: 'TherapyType',
) -> None:
    """Sprawdza, czy eksport danych RODO zawiera sekcje kliniczne, wizyty, odcinki i dokumenty pacjenta."""
    # Arrange
    Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=timezone.now(),
        end_at=timezone.now() + timedelta(minutes=45),
        status=VisitStatus.SCHEDULED,
    )
    token: str = str(RefreshToken.for_user(patient.user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    # Act
    response = api_client.post('/api/v1/me/data-export/', {}, format='json')
    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert 'profile' in response.data
    assert 'consents' in response.data
    assert 'visits' in response.data
    assert 'episodes' in response.data
    assert 'documents' in response.data
    assert 'exercise_assignments' in response.data
    assert len(response.data['visits']) == 1


@pytest.mark.django_db
def test_data_export_includes_notification_prefs_and_device_fingerprint(
    api_client: 'APIClient',
    patient: 'PatientProfile',
) -> None:
    """Sprawdza, czy eksport danych zawiera preferencje powiadomień i zanonimizowane tokeny urządzeń."""
    # Arrange
    ensure_default_preferences(patient.user)
    NotificationPreference.objects.filter(
        user=patient.user,
        pref_key=NotificationPreferenceKey.WAITLIST,
    ).update(enabled=False)
    DeviceToken.objects.create(
        user=patient.user,
        expo_push_token='ExponentPushToken[physiocare-export]',
        platform='android',
    )
    token: str = str(RefreshToken.for_user(patient.user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    # Act
    response = api_client.post('/api/v1/me/data-export/', {}, format='json')
    # Assert
    assert response.status_code == status.HTTP_200_OK
    prefs: dict[str, bool] = {item['pref_key']: item['enabled'] for item in response.data['notification_preferences']}
    assert set(prefs) == {
        'visit_reminder',
        'visit_change',
        'waitlist',
        'exercise_reminder',
        'new_document',
        'review_request',
    }
    assert prefs['waitlist'] is False
    devices = response.data['device_tokens']
    assert len(devices) == 1
    assert devices[0]['platform'] == 'android'
    assert 'expo_push_token' not in devices[0]
    assert devices[0]['token_fingerprint'].startswith('…')
    assert 'notification_deliveries' in response.data


