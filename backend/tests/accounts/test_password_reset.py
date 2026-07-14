import hashlib
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import PasswordResetToken

User = get_user_model()


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


@pytest.mark.django_db
def test_password_reset_token_expires():
    user = User.objects.create_user(
        email='reset@physiocare.test',
        password='old-pass-123',
        role='PATIENT',
        first_name='Test',
        last_name='User',
    )
    raw_token = 'expired-token-value'
    PasswordResetToken.objects.create(
        user=user,
        token_hash=_hash_token(raw_token),
        expires_at=timezone.now() - timedelta(minutes=1),
    )

    client = APIClient()
    response = client.post(
        '/api/v1/auth/password-reset/confirm/',
        {'token': raw_token, 'new_password': 'new-pass-456'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    user.refresh_from_db()
    assert user.check_password('old-pass-123')
