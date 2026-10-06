import pyotp
import pytest
from rest_framework import status

from accounts.email_codes import issue_email_code
from accounts.mfa import (
    generate_backup_codes,
    generate_totp_secret,
    issue_mfa_preauth_token,
    issue_mfa_setup_token,
)
from accounts.models import EmailCodePurpose, UserMFA


@pytest.mark.django_db
def test_mfa_setup_returns_secret_and_qr_svg(api_client: object, therapist: object) -> None:
    """Sprawdza, czy konfiguracja 2FA zwraca sekret TOTP oraz kod QR w formacie SVG."""
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
def test_mfa_setup_already_enabled_returns_400(api_client: object, therapist: object) -> None:
    """Sprawdza, czy próba ponownej konfiguracji 2FA dla aktywnej usługi zwraca błąd 400."""
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
    api_client: object, therapist: object,
) -> None:
    """Sprawdza aktywację 2FA za pomocą poprawnego kodu TOTP i generowanie kodów zapasowych."""
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
def test_mfa_enable_with_invalid_totp_returns_400(api_client: object, therapist: object) -> None:
    """Sprawdza odrzucenie włączenia 2FA przy podaniu nieprawidłowego kodu TOTP."""
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
def test_mfa_login_flow_step1_requires_2fa_token(api_client: object, therapist: object) -> None:
    """Sprawdza krok 1 logowania: żądanie drugiego składnika 2FA przy włączonej usłudze."""
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
def test_mfa_login_flow_step2_with_valid_totp(api_client: object, therapist: object) -> None:
    """Sprawdza krok 2 logowania: pomyślne uwierzytelnienie kodem TOTP."""
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
def test_mfa_login_flow_step2_with_backup_code(api_client: object, therapist: object) -> None:
    """Sprawdza krok 2 logowania: logowanie za pomocą kodu zapasowego."""
    # Arrange
    secret = generate_totp_secret()
    # Act
    raw_codes, hashed_codes = generate_backup_codes(8)
    UserMFA.objects.create(
        user=therapist.user,
        secret_key=secret,
        is_enabled=True,
        backup_codes=hashed_codes,
    )
    mfa_token = issue_mfa_preauth_token(therapist.user)
    backup_code = raw_codes[0]

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
def test_mfa_login_flow_step2_backup_code_is_single_use(api_client: object, therapist: object) -> None:
    """Sprawdza jednorazowość kodu zapasowego i blokadę przy ponownej próbie."""
    # Arrange
    secret = generate_totp_secret()
    # Act
    raw_codes, hashed_codes = generate_backup_codes(8)
    UserMFA.objects.create(
        user=therapist.user,
        secret_key=secret,
        is_enabled=True,
        backup_codes=hashed_codes,
    )
    backup_code = raw_codes[0]

    mfa_token1 = issue_mfa_preauth_token(therapist.user)
    resp1 = api_client.post(
        '/api/v1/auth/2fa/login/',
        data={'mfa_token': mfa_token1, 'code': backup_code},
        format='json',
    )
    # Assert
    assert resp1.status_code == status.HTTP_200_OK

    mfa_token2 = issue_mfa_preauth_token(therapist.user)
    resp2 = api_client.post(
        '/api/v1/auth/2fa/login/',
        data={'mfa_token': mfa_token2, 'code': backup_code},
        format='json',
    )

    assert resp2.status_code == status.HTTP_401_UNAUTHORIZED
    assert resp2.data['error']['code'] == 'AUTH_MFA_INVALID_CODE'


@pytest.mark.django_db
def test_mfa_login_flow_step2_invalid_code_returns_401(api_client: object, therapist: object) -> None:
    """Sprawdza błąd 401 przy podaniu błędnego kodu w kroku 2 logowania."""
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
def test_mfa_disable_with_valid_password(api_client: object, therapist: object) -> None:
    """Sprawdza wyłączenie 2FA przy podaniu poprawnego hasła użytkownika."""
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
def test_mfa_disable_wrong_password_returns_401(api_client: object, therapist: object) -> None:
    """Sprawdza odrzucenie próby wyłączenia 2FA przy podaniu błędnego hasła."""
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
def test_mfa_status_endpoint(api_client: object, therapist: object, patient: object) -> None:
    """Sprawdza działanie punktu końcowego statusu usługi 2FA dla fizjoterapeuty i pacjenta."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)
    # Act
    res_therapist = api_client.get('/api/v1/auth/2fa/status/')
    # Assert
    assert res_therapist.status_code == status.HTTP_200_OK
    assert res_therapist.data['is_enabled'] is False
    assert res_therapist.data['mfa_required_for_role'] is True

    UserMFA.objects.create(
        user=therapist.user,
        secret_key=generate_totp_secret(),
        is_enabled=True,
    )
    res_therapist_enabled = api_client.get('/api/v1/auth/2fa/status/')
    assert res_therapist_enabled.data['is_enabled'] is True

    api_client.force_authenticate(user=patient.user)
    res_patient = api_client.get('/api/v1/auth/2fa/status/')
    assert res_patient.status_code == status.HTTP_200_OK
    assert res_patient.data['is_enabled'] is False
    assert res_patient.data['mfa_required_for_role'] is False


@pytest.mark.django_db
def test_mfa_secret_key_is_encrypted_in_db(therapist: object) -> None:
    """Sprawdza, że sekret TOTP jest szyfrowany w bazie danych (F-02)."""
    from django.db import connection

    plain_secret = generate_totp_secret()
    mfa = UserMFA.objects.create(
        user=therapist.user,
        secret_key=plain_secret,
        is_enabled=True,
    )

    # Odczyt bezpośrednio przez raw SQL w bazie danych
    with connection.cursor() as cursor:
        cursor.execute('SELECT secret_key FROM user_mfa WHERE id = %s', [str(mfa.id)])
        db_raw_value = cursor.fetchone()[0]

    # Wartość w bazie danych MUSI być zaszyfrowana (Fernet ciphertext zaczynający się od gAAAAA)
    assert db_raw_value.startswith('gAAAAA')
    assert db_raw_value != plain_secret

    # Odczyt przez model Django MUSI automatycznie odszyfrować wartość
    loaded = UserMFA.objects.get(id=mfa.id)
    assert loaded.secret_key == plain_secret


@pytest.mark.django_db
def test_password_login_therapist_without_mfa_returns_403(api_client: object, therapist: object) -> None:
    """Sprawdza zablokowanie logowania hasłem dla fizjoterapeuty bez włączonego MFA (F-03)."""
    from django.core.cache import cache

    cache.clear()
    response = api_client.post(
        '/api/v1/auth/login/',
        data={'email': therapist.user.email, 'password': 'test-pass'},
        format='json',
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['error']['code'] == 'AUTH_MFA_SETUP_REQUIRED'
    assert response.data['error']['details']['mfa_required'] is True


@pytest.mark.django_db
def test_mfa_setup_token_allows_configuration_without_authenticated_session(
    api_client: object, therapist: object,
) -> None:
    """Sprawdza ograniczoną konfigurację MFA po logowaniu bez tworzenia sesji panelu."""
    setup_token = issue_mfa_setup_token(therapist.user)
    email_code = issue_email_code(
        user=therapist.user,
        purpose=EmailCodePurpose.MFA_SETUP,
    )

    setup_response = api_client.post(
        '/api/v1/auth/2fa/setup/',
        data={'mfa_setup_token': setup_token, 'email_code': email_code},
        format='json',
    )

    assert setup_response.status_code == status.HTTP_200_OK
    assert 'access' not in setup_response.data
    secret = setup_response.data['secret_key']

    enable_response = api_client.post(
        '/api/v1/auth/2fa/enable/',
        data={'mfa_setup_token': setup_token, 'code': pyotp.TOTP(secret).now()},
        format='json',
    )

    assert enable_response.status_code == status.HTTP_200_OK
    assert UserMFA.objects.get(user=therapist.user).is_enabled is True
    assert not api_client.cookies.get('access_token')


@pytest.mark.django_db
def test_expired_or_invalid_mfa_setup_token_is_rejected(api_client: object) -> None:
    """Sprawdza, że konfiguracja MFA wymaga ważnego tokenu setup."""
    response = api_client.post(
        '/api/v1/auth/2fa/setup/',
        data={'mfa_setup_token': 'invalid-token'},
        format='json',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['error']['code'] == 'AUTH_MFA_SETUP_TOKEN_INVALID'


@pytest.mark.django_db
def test_password_login_staff_admin_without_mfa_returns_403(api_client: object) -> None:
    """Sprawdza zablokowanie logowania hasłem dla konta administratora/staff bez MFA (F-03)."""
    from django.contrib.auth import get_user_model
    from django.core.cache import cache
    from django.utils import timezone

    cache.clear()
    user_model = get_user_model()
    admin_user = user_model.objects.create_user(
        email='admin@physiocare.test',
        password='AdminPassword123!',
        is_staff=True,
        email_verified_at=timezone.now(),
    )

    response = api_client.post(
        '/api/v1/auth/login/',
        data={'email': admin_user.email, 'password': 'AdminPassword123!'},
        format='json',
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['error']['code'] == 'AUTH_MFA_SETUP_REQUIRED'
    assert response.data['error']['details']['mfa_required'] is True


@pytest.mark.django_db
def test_password_login_patient_without_mfa_succeeds(api_client: object, patient: object) -> None:
    """Sprawdza, że pacjent bez MFA może logować się standardowo hasłem."""
    from django.core.cache import cache

    cache.clear()
    response = api_client.post(
        '/api/v1/auth/login/',
        data={'email': patient.user.email, 'password': 'test-pass'},
        format='json',
    )
    assert response.status_code == status.HTTP_200_OK
    assert 'access' in response.data
    assert 'refresh' in response.data
    assert response.data.get('mfa_required') is not True


@pytest.mark.django_db
def test_mfa_setup_email_template_rendering_and_attachment(
    therapist: object, settings: object
) -> None:
    """Sprawdza renderowanie szablonu HTML wiadomości konfiguracji 2FA i załącznik logo."""
    from django.core import mail

    from accounts.email_codes import send_mfa_setup_code

    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox.clear()

    ok = send_mfa_setup_code(user=therapist.user)
    assert ok is True
    assert len(mail.outbox) == 1

    email_msg = mail.outbox[0]
    assert email_msg.subject == 'PhysioCare - potwierdź konfigurację MFA'
    assert 'Jan' in email_msg.body
    assert 'PhysioCare' in email_msg.body

    assert len(email_msg.alternatives) == 1
    html_content, mimetype = email_msg.alternatives[0]
    assert mimetype == 'text/html'
    assert 'Cześć Jan' in html_content
    assert 'Kod konfiguracji 2FA' in html_content
    assert 'data:image/png;base64,' in html_content
    assert 'Twój kod konfiguracji 2FA:' in html_content
    assert len(email_msg.attachments) == 0
