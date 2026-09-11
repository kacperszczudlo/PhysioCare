import pyotp
import pytest
from rest_framework import status

from accounts.mfa import (
    generate_backup_codes,
    generate_totp_secret,
    issue_mfa_preauth_token,
)
from accounts.models import UserMFA


@pytest.mark.django_db
def test_mfa_setup_returns_secret_and_qr_svg(api_client, therapist):
    # Arrange
    api_client.force_authenticate(user=therapist.user)

    # Act
    response = api_client.post('/api/v1/auth/2fa/setup/')

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert 'secret_key' in response.data
    assert 'otpauth_url' in response.data
    assert 'qr_code_svg' in response.data
    assert response.data['qr_code_svg'].startswith('<svg') or 'xmlns' in response.data['qr_code_svg']
    assert UserMFA.objects.filter(user=therapist.user, is_enabled=False).exists()


@pytest.mark.django_db
def test_mfa_setup_already_enabled_returns_400(api_client, therapist):
    # Arrange
    UserMFA.objects.create(
        user=therapist.user,
        secret_key=generate_totp_secret(),
        is_enabled=True,
    )
    api_client.force_authenticate(user=therapist.user)

    # Act
    response = api_client.post('/api/v1/auth/2fa/setup/')

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error']['code'] == 'AUTH_MFA_ALREADY_ENABLED'


@pytest.mark.django_db
def test_mfa_enable_with_valid_totp_activates_2fa_and_returns_backup_codes(
    api_client, therapist,
):
    # Arrange
    secret = generate_totp_secret()
    UserMFA.objects.create(user=therapist.user, secret_key=secret, is_enabled=False)
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()

    api_client.force_authenticate(user=therapist.user)

    # Act
    response = api_client.post(
        '/api/v1/auth/2fa/enable/',
        data={'code': valid_code},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert 'backup_codes' in response.data
    assert len(response.data['backup_codes']) == 8

    mfa = UserMFA.objects.get(user=therapist.user)
    assert mfa.is_enabled is True
    assert len(mfa.backup_codes) == 8


@pytest.mark.django_db
def test_mfa_enable_with_invalid_totp_returns_400(api_client, therapist):
    # Arrange
    secret = generate_totp_secret()
    UserMFA.objects.create(user=therapist.user, secret_key=secret, is_enabled=False)
    api_client.force_authenticate(user=therapist.user)

    # Act
    response = api_client.post(
        '/api/v1/auth/2fa/enable/',
        data={'code': '000000'},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error']['code'] == 'AUTH_MFA_INVALID_CODE'

    mfa = UserMFA.objects.get(user=therapist.user)
    assert mfa.is_enabled is False


@pytest.mark.django_db
def test_mfa_login_flow_step1_requires_2fa_token(api_client, therapist):
    # Arrange
    secret = generate_totp_secret()
    UserMFA.objects.create(user=therapist.user, secret_key=secret, is_enabled=True)

    # Act
    response = api_client.post(
        '/api/v1/auth/login/',
        data={'email': therapist.user.email, 'password': 'test-pass'},
        format='json',
    )


    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get('mfa_required') is True
    assert 'mfa_token' in response.data
    assert 'access' not in response.data


@pytest.mark.django_db
def test_mfa_login_flow_step2_with_valid_totp(api_client, therapist):
    # Arrange
    secret = generate_totp_secret()
    UserMFA.objects.create(user=therapist.user, secret_key=secret, is_enabled=True)

    mfa_token = issue_mfa_preauth_token(therapist.user)
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()

    # Act
    response = api_client.post(
        '/api/v1/auth/2fa/login/',
        data={'mfa_token': mfa_token, 'code': valid_code},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert 'user' in response.data
    assert response.data['user']['email'] == therapist.user.email


@pytest.mark.django_db
def test_mfa_login_flow_step2_with_backup_code(api_client, therapist):
    # Arrange
    secret = generate_totp_secret()
    raw_codes, hashed_codes = generate_backup_codes(8)
    UserMFA.objects.create(
        user=therapist.user,
        secret_key=secret,
        is_enabled=True,
        backup_codes=hashed_codes,
    )
    mfa_token = issue_mfa_preauth_token(therapist.user)
    backup_code = raw_codes[0]

    # Act
    response = api_client.post(
        '/api/v1/auth/2fa/login/',
        data={'mfa_token': mfa_token, 'code': backup_code},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert 'user' in response.data

    mfa = UserMFA.objects.get(user=therapist.user)
    assert len(mfa.backup_codes) == 7


@pytest.mark.django_db
def test_mfa_login_flow_step2_backup_code_is_single_use(api_client, therapist):
    # Arrange
    secret = generate_totp_secret()
    raw_codes, hashed_codes = generate_backup_codes(8)
    UserMFA.objects.create(
        user=therapist.user,
        secret_key=secret,
        is_enabled=True,
        backup_codes=hashed_codes,
    )
    backup_code = raw_codes[0]

    # First attempt (uses code)
    mfa_token1 = issue_mfa_preauth_token(therapist.user)
    resp1 = api_client.post(
        '/api/v1/auth/2fa/login/',
        data={'mfa_token': mfa_token1, 'code': backup_code},
        format='json',
    )
    assert resp1.status_code == status.HTTP_200_OK

    # Second attempt (same backup code)
    mfa_token2 = issue_mfa_preauth_token(therapist.user)
    resp2 = api_client.post(
        '/api/v1/auth/2fa/login/',
        data={'mfa_token': mfa_token2, 'code': backup_code},
        format='json',
    )

    # Assert second attempt failed
    assert resp2.status_code == status.HTTP_401_UNAUTHORIZED
    assert resp2.data['error']['code'] == 'AUTH_MFA_INVALID_CODE'


@pytest.mark.django_db
def test_mfa_login_flow_step2_invalid_code_returns_401(api_client, therapist):
    # Arrange
    secret = generate_totp_secret()
    UserMFA.objects.create(user=therapist.user, secret_key=secret, is_enabled=True)
    mfa_token = issue_mfa_preauth_token(therapist.user)

    # Act
    response = api_client.post(
        '/api/v1/auth/2fa/login/',
        data={'mfa_token': mfa_token, 'code': '123456'},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['error']['code'] == 'AUTH_MFA_INVALID_CODE'


@pytest.mark.django_db
def test_mfa_disable_with_valid_password(api_client, therapist):
    # Arrange
    secret = generate_totp_secret()
    UserMFA.objects.create(user=therapist.user, secret_key=secret, is_enabled=True)
    api_client.force_authenticate(user=therapist.user)

    # Act
    response = api_client.post(
        '/api/v1/auth/2fa/disable/',
        data={'password': 'test-pass'},
        format='json',
    )


    # Assert
    assert response.status_code == status.HTTP_200_OK
    mfa = UserMFA.objects.get(user=therapist.user)
    assert mfa.is_enabled is False


@pytest.mark.django_db
def test_mfa_disable_wrong_password_returns_401(api_client, therapist):
    # Arrange
    secret = generate_totp_secret()
    UserMFA.objects.create(user=therapist.user, secret_key=secret, is_enabled=True)
    api_client.force_authenticate(user=therapist.user)

    # Act
    response = api_client.post(
        '/api/v1/auth/2fa/disable/',
        data={'password': 'WrongPassword999!'},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    mfa = UserMFA.objects.get(user=therapist.user)
    assert mfa.is_enabled is True


@pytest.mark.django_db
def test_mfa_status_endpoint(api_client, therapist, patient):
    # Test therapist with 2FA disabled
    api_client.force_authenticate(user=therapist.user)
    res_therapist = api_client.get('/api/v1/auth/2fa/status/')
    assert res_therapist.status_code == status.HTTP_200_OK
    assert res_therapist.data['is_enabled'] is False
    assert res_therapist.data['mfa_required_for_role'] is True

    # Enable 2FA for therapist
    UserMFA.objects.create(
        user=therapist.user,
        secret_key=generate_totp_secret(),
        is_enabled=True,
    )
    res_therapist_enabled = api_client.get('/api/v1/auth/2fa/status/')
    assert res_therapist_enabled.data['is_enabled'] is True

    # Test patient status
    api_client.force_authenticate(user=patient.user)
    res_patient = api_client.get('/api/v1/auth/2fa/status/')
    assert res_patient.status_code == status.HTTP_200_OK
    assert res_patient.data['is_enabled'] is False
    assert res_patient.data['mfa_required_for_role'] is False
