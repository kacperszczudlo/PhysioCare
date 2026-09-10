import pytest
from django.core.cache import cache
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from privacy.models import AccountDeletionRequest


@pytest.fixture(autouse=True)
def _clear_auth_throttle():
    cache.clear()
    yield
    cache.clear()


def _login(api_client, email, password='test-pass'):
    return api_client.post(
        '/api/v1/auth/login/',
        {'email': email, 'password': password},
        format='json',
    )


@pytest.mark.django_db
def test_login_includes_tokens_by_default(api_client, patient):
    response = _login(api_client, patient.user.email)
    assert response.status_code == status.HTTP_200_OK
    assert 'access' in response.data
    assert 'refresh' in response.data


@pytest.mark.django_db
def test_login_cookie_delivery_omits_body_tokens(api_client, therapist):
    response = api_client.post(
        '/api/v1/auth/login/',
        {
            'email': therapist.user.email,
            'password': 'test-pass',
            'token_delivery': 'cookie',
        },
        format='json',
    )
    assert response.status_code == status.HTTP_200_OK
    assert 'access' not in response.data
    assert 'refresh' not in response.data
    assert 'access_token' in response.cookies


@pytest.mark.django_db
def test_logout_blacklists_refresh_token(api_client, patient):
    login = _login(api_client, patient.user.email)
    refresh = login.data['refresh']

    logout = api_client.post('/api/v1/auth/logout/', {'refresh': refresh}, format='json')
    assert logout.status_code == status.HTTP_200_OK

    reuse = api_client.post('/api/v1/auth/refresh/', {'refresh': refresh}, format='json')
    assert reuse.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_refresh_rotation_rejects_old_token(api_client, patient):
    login = _login(api_client, patient.user.email)
    old_refresh = login.data['refresh']

    rotated = api_client.post('/api/v1/auth/refresh/', {'refresh': old_refresh}, format='json')
    assert rotated.status_code == status.HTTP_200_OK
    assert rotated.data['refresh'] != old_refresh

    reuse = api_client.post('/api/v1/auth/refresh/', {'refresh': old_refresh}, format='json')
    assert reuse.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_password_change_blacklists_refresh(api_client, patient):
    login = _login(api_client, patient.user.email)
    refresh = login.data['refresh']
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')

    change = api_client.post(
        '/api/v1/auth/password-change/',
        {'current_password': 'test-pass', 'new_password': 'New-pass-123!'},
        format='json',
    )
    assert change.status_code == status.HTTP_200_OK

    reuse = api_client.post('/api/v1/auth/refresh/', {'refresh': refresh}, format='json')
    assert reuse.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_account_deletion_persists_and_deactivates(api_client, patient):
    token = str(RefreshToken.for_user(patient.user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    original_email = patient.user.email

    response = api_client.post(
        '/api/v1/me/account-deletion-request/',
        {'reason': 'Nie korzystam z aplikacji'},
        format='json',
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert AccountDeletionRequest.objects.filter(user=patient.user).exists()
    deletion = AccountDeletionRequest.objects.get(user=patient.user)
    assert deletion.reason == 'Nie korzystam z aplikacji'
    patient.user.refresh_from_db()
    assert patient.user.is_active is False
    assert patient.user.email == f'deleted-{patient.user.pk}@deleted.invalid'
    assert patient.user.email != original_email
    assert not patient.user.has_usable_password()
    # E-mail is free for a new registration.
    assert not type(patient.user).objects.filter(email__iexact=original_email, is_active=True).exists()
