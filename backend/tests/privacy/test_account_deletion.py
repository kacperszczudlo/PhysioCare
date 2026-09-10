import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from notifications.models import DeviceToken
from privacy.models import AccountDeletionRequest

User = get_user_model()

SAMPLE_TOKEN = 'ExponentPushToken[physiocare-deletion-test]'


@pytest.mark.django_db
def test_account_deletion_anonymizes_and_frees_email(api_client, patient, therapist):
    user = patient.user
    original_email = user.email
    DeviceToken.objects.create(
        user=user,
        expo_push_token=SAMPLE_TOKEN,
        platform='android',
        is_active=True,
    )
    token = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    response = api_client.post(
        '/api/v1/me/account-deletion-request/',
        {'reason': 'Problemy techniczne'},
        format='json',
    )
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

    # Same e-mail can register again as a new patient.
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
def test_legacy_inactive_email_can_reregister(api_client, patient, therapist):
    """Accounts deactivated before anonymization still block e-mail — reclaim on register."""
    user = patient.user
    original_email = user.email
    user.is_active = False
    user.save(update_fields=['is_active', 'updated_at'])
    AccountDeletionRequest.objects.get_or_create(user=user)

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
    assert register.status_code in (
        status.HTTP_201_CREATED,
        status.HTTP_200_OK,
        status.HTTP_202_ACCEPTED,
    )
    user.refresh_from_db()
    assert user.email.startswith('deleted-')
    assert User.objects.filter(email__iexact=original_email, is_active=True).count() == 1
