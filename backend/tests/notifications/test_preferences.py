import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.serializers import PatientRegistrationSerializer
from notifications.keys import CANONICAL_PREF_KEYS
from notifications.models import NotificationPreference


def _patient_auth(api_client: object, patient: object) -> None:
    """Ustawia nagłówek autoryzacji Bearer JWT dla pacjenta."""
    token: str = str(RefreshToken.for_user(patient.user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')


def _pref_map(payload: list[dict[str, object]]) -> dict[str, bool]:
    """Przekształca listę zagnieżdżonych preferencji w słownik klucz-wartość."""
    return {str(item['pref_key']): bool(item['enabled']) for item in payload}


@pytest.mark.django_db
def test_get_seeds_canonical_preferences_enabled(
    api_client: object, patient: object,
) -> None:
    """Sprawdza domyślną inicjalizację kanonicznych preferencji powiadomień po pierwszym zapytaniu GET."""
    # Arrange
    _patient_auth(api_client, patient)

    response: object = api_client.get('/api/v1/me/notification-preferences/')

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert [item['pref_key'] for item in response.data] == list(CANONICAL_PREF_KEYS)
    assert all(item['enabled'] is True for item in response.data)
    assert NotificationPreference.objects.filter(user=patient.user).count() == len(
        CANONICAL_PREF_KEYS
    )


@pytest.mark.django_db
def test_patch_updates_known_key(api_client: object, patient: object) -> None:
    """Sprawdza aktualizację znanej preferencji powiadomień metodą PATCH."""
    # Arrange
    _patient_auth(api_client, patient)

    response: object = api_client.patch(
        '/api/v1/me/notification-preferences/',
        {'visit_reminder': False},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    prefs: dict[str, bool] = _pref_map(response.data)
    assert prefs['visit_reminder'] is False
    assert prefs['visit_change'] is True
    assert set(prefs) == set(CANONICAL_PREF_KEYS)


@pytest.mark.django_db
def test_patch_accepts_preferences_wrapper(
    api_client: object, patient: object,
) -> None:
    """Sprawdza akceptację struktury ze słownikiem 'preferences' w ciele zapytania PATCH."""
    # Arrange
    _patient_auth(api_client, patient)

    response: object = api_client.patch(
        '/api/v1/me/notification-preferences/',
        {'preferences': {'waitlist': False, 'new_document': False}},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    prefs: dict[str, bool] = _pref_map(response.data)
    assert prefs['waitlist'] is False
    assert prefs['new_document'] is False
    assert prefs['exercise_reminder'] is True


@pytest.mark.django_db
def test_patch_rejects_unknown_keys(api_client: object, patient: object) -> None:
    """Sprawdza odrzucenie nieznanych kluczy preferencji przy aktualizacji."""
    # Arrange
    _patient_auth(api_client, patient)

    response: object = api_client.patch(
        '/api/v1/me/notification-preferences/',
        {'visit_reminders': True, 'visit_reminder': False},
        format='json',
    )

    # Assert
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
def test_therapist_cannot_access_notification_preferences(
    api_client: object, therapist: object,
) -> None:
    """Sprawdza odrzucenie próby dostępu do preferencji powiadomień przez fizjoterapeutę."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)

    response: object = api_client.get('/api/v1/me/notification-preferences/')

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_patient_registration_seeds_notification_preferences(therapist: object) -> None:
    """Sprawdza automatyczne tworzenie zestawu preferencji powiadomień podczas rejestracji pacjenta."""
    # Arrange
    serializer: PatientRegistrationSerializer = PatientRegistrationSerializer(
        data={
            'email': 'nowy.pacjent@physiocare.test',
            'password': 'SecurePass123!',
            'first_name': 'Jan',
            'last_name': 'Kowalski',
            'therapist_id': str(therapist.id),
            'consents': {'terms': True, 'medical_data': True},
        }
    )
    # Assert
    assert serializer.is_valid(), serializer.errors
    user: object = serializer.save()

    keys: set[str] = set(
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

