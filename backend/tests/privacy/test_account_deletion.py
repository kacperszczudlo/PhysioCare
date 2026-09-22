from typing import TYPE_CHECKING

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from notifications.models import DeviceToken
from privacy.models import AccountDeletionRequest

if TYPE_CHECKING:
    from rest_framework.test import APIClient

    from patients.models import PatientProfile
    from therapists.models import TherapistProfile

User = get_user_model()

SAMPLE_TOKEN: str = 'ExponentPushToken[physiocare-deletion-test]'


@pytest.mark.django_db
def test_account_deletion_anonymizes_and_frees_email(
    api_client: 'APIClient',
    patient: 'PatientProfile',
    therapist: 'TherapistProfile',
) -> None:
    """Sprawdza anonimizację danych osobowych pacjenta oraz zwolnienie adresu e-mail po usunięciu konta."""
    # Arrange
    user = patient.user
    original_email: str = user.email
    DeviceToken.objects.create(
        user=user,
        expo_push_token=SAMPLE_TOKEN,
        platform='android',
        is_active=True,
    )
    token: str = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    # Act
    response = api_client.post(
        '/api/v1/me/account-deletion-request/',
        {'reason': 'Problemy techniczne'},
        format='json',
    )
    # Assert
    assert response.status_code == status.HTTP_202_ACCEPTED

    user.refresh_from_db()
    patient.refresh_from_db()
    deletion = AccountDeletionRequest.objects.get(user=user)

    assert user.is_active is False
    assert user.email == f'deleted-{user.pk}@deleted.invalid'
    assert user.first_name == 'Usunięte'
    assert user.last_name == 'Konto'
    assert user.google_sub is None
    assert patient.phone == ''
    assert patient.pesel is None
    assert deletion.reason == 'Problemy techniczne'
    assert original_email in deletion.notes
    assert DeviceToken.objects.filter(user=user, is_active=True).count() == 0

    api_client.credentials()
    register = api_client.post(
        '/api/v1/auth/register/patient/',
        {
            'email': original_email,
            'password': 'StrongPass1!',
            'first_name': 'Nowy',
            'last_name': 'Pacjent',
            'therapist_id': str(therapist.id),
            'consents': {'terms': True, 'medical_data': True},
        },
        format='json',
    )
    assert register.status_code in (
        status.HTTP_201_CREATED,
        status.HTTP_200_OK,
        status.HTTP_202_ACCEPTED,
    )
    assert User.objects.filter(email__iexact=original_email, is_active=True).exists()


@pytest.mark.django_db
def test_legacy_inactive_email_can_reregister(
    api_client: 'APIClient',
    patient: 'PatientProfile',
    therapist: 'TherapistProfile',
) -> None:
    """Sprawdza możliwość ponownej rejestracji na e-mail z nieaktywnego konta historycznego."""
    # Arrange
    from django.core.cache import cache
    cache.clear()

    user = patient.user
    original_email: str = user.email
    user.is_active = False
    user.save(update_fields=['is_active', 'updated_at'])
    AccountDeletionRequest.objects.get_or_create(user=user)

    # Act
    register = api_client.post(
        '/api/v1/auth/register/patient/',
        {
            'email': original_email,
            'password': 'StrongPass1!',
            'first_name': 'Ponowny',
            'last_name': 'Start',
            'therapist_id': str(therapist.id),
            'consents': {'terms': True, 'medical_data': True},
        },
        format='json',
    )
    # Assert
    assert register.status_code in (
        status.HTTP_201_CREATED,
        status.HTTP_200_OK,
        status.HTTP_202_ACCEPTED,
    )
    user.refresh_from_db()
    assert user.email.startswith('deleted-')
    assert User.objects.filter(email__iexact=original_email, is_active=True).count() == 1


@pytest.mark.django_db
def test_privacy_models_helpers(patient: 'PatientProfile') -> None:
    """Sprawdza działanie metod pomocniczych reprezentacji i statusu w modelach prywatności."""
    # Arrange
    from django.utils import timezone

    from privacy.models import Consent, ConsentType

    consent = Consent.objects.create(
        user=patient.user,
        consent_type=ConsentType.TERMS_REQUIRED,
        granted=True,
    )
    # Assert
    assert str(consent) == f'{patient.user.email} - TERMS_REQUIRED'
    assert consent.is_required_consent() is True

    optional_consent = Consent.objects.create(
        user=patient.user,
        consent_type=ConsentType.MARKETING_OPTIONAL,
        granted=False,
    )
    assert optional_consent.is_required_consent() is False

    req = AccountDeletionRequest.objects.create(user=patient.user, reason='Test')
    assert str(req) == f'Deletion request {patient.user.email}'
    assert req.is_processed() is False

    req.processed_at = timezone.now()
    req.save()
    assert req.is_processed() is True


