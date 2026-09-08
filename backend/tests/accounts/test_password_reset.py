import hashlib
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import PasswordResetToken

User = get_user_model()


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


@pytest.fixture(autouse=True)
def _clear_password_reset_throttle():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def patient_user(db):
    return User.objects.create_user(
        email='reset@physiocare.test',
        password='old-pass-123!',
        role='PATIENT',
        first_name='Test',
        last_name='User',
    )


@pytest.mark.django_db
def test_password_reset_token_expires(api_client, patient_user):
    raw_token = 'expired-token-value'
    PasswordResetToken.objects.create(
        user=patient_user,
        token_hash=_hash_token(raw_token),
        expires_at=timezone.now() - timedelta(minutes=1),
    )

    response = api_client.post(
        '/api/v1/auth/password-reset/confirm/',
        {'token': raw_token, 'new_password': 'new-pass-456!'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    patient_user.refresh_from_db()
    assert patient_user.check_password('old-pass-123!')


@pytest.mark.django_db
def test_password_reset_request_sends_web_link(api_client, patient_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    settings.FRONTEND_URL = 'http://localhost:5173'

    response = api_client.post(
        '/api/v1/auth/password-reset/request/',
        {'email': patient_user.email, 'client': 'web'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 1
    body = mail.outbox[0].body
    assert 'http://localhost:5173/reset?token=' in body
    assert patient_user.email in mail.outbox[0].to
    html = mail.outbox[0].alternatives[0][0]
    assert 'Ustaw nowe hasło' in html
    assert PasswordResetToken.objects.filter(user=patient_user, used_at__isnull=True).exists()


@pytest.mark.django_db
def test_password_reset_request_sends_mobile_deep_link(api_client, patient_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    settings.MOBILE_RESET_URL_BASE = 'physiocare://'
    settings.FRONTEND_URL = 'http://localhost:5173'

    response = api_client.post(
        '/api/v1/auth/password-reset/request/',
        {'email': patient_user.email, 'client': 'mobile'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 1
    assert 'physiocare://password-reset?token=' in mail.outbox[0].body
    assert 'http://localhost:5173/reset?token=' in mail.outbox[0].body


@pytest.mark.django_db
def test_password_reset_request_email_iexact(api_client, patient_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

    response = api_client.post(
        '/api/v1/auth/password-reset/request/',
        {'email': patient_user.email.upper(), 'client': 'web'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_password_reset_request_unknown_email_no_mail(api_client, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

    response = api_client.post(
        '/api/v1/auth/password-reset/request/',
        {'email': 'nobody@physiocare.test', 'client': 'web'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert 'Jeśli konto istnieje' in response.data['detail']
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_password_reset_confirm_success(api_client, patient_user):
    raw_token = 'valid-reset-token-value'
    PasswordResetToken.objects.create(
        user=patient_user,
        token_hash=_hash_token(raw_token),
        expires_at=timezone.now() + timedelta(minutes=30),
    )

    response = api_client.post(
        '/api/v1/auth/password-reset/confirm/',
        {'token': raw_token, 'new_password': 'new-pass-456!'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    patient_user.refresh_from_db()
    assert patient_user.check_password('new-pass-456!')
    token = PasswordResetToken.objects.get(token_hash=_hash_token(raw_token))
    assert token.used_at is not None


@pytest.mark.django_db
def test_password_reset_confirm_missing_token(api_client):
    response = api_client.post(
        '/api/v1/auth/password-reset/confirm/',
        {'token': '', 'new_password': 'new-pass-456!'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
