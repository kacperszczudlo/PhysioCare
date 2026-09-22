from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.email_codes import hash_email_code, issue_email_code, issue_password_reset_token
from accounts.models import EmailCode, EmailCodePurpose, PasswordResetToken

User = get_user_model()


@pytest.fixture(autouse=True)
def _clear_password_reset_throttle(settings: object) -> object:
    """Czyści limity zapytania throttle dla zapytań o reset hasła."""
    cache.clear()
    rates = settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']
    previous = rates.get('password_reset')
    rates['password_reset'] = '1000/minute'
    yield
    if previous is not None:
        rates['password_reset'] = previous
    cache.clear()


@pytest.fixture
def api_client() -> APIClient:
    """Fixture klienta API REST."""
    return APIClient()


@pytest.fixture
def patient_user(db: object) -> object:
    """Fixture konta pacjenta do testów resetowania hasła."""
    return User.objects.create_user(
        email='reset@physiocare.test',
        password='old-pass-123!',
        role='PATIENT',
        first_name='Test',
        last_name='User',
        email_verified_at=timezone.now(),
    )


@pytest.mark.django_db
def test_password_reset_code_expires(api_client: APIClient, patient_user: object) -> None:
    """Sprawdza odrzucanie przedawnionego kodu resetu hasła."""
    # Arrange
    raw = '123456'
    EmailCode.objects.create(
        user=patient_user,
        purpose=EmailCodePurpose.PASSWORD_RESET,
        code_hash=hash_email_code(raw),
        expires_at=timezone.now() - timedelta(minutes=1),
    )

    # Act
    response = api_client.post(
        '/api/v1/auth/password-reset/verify/',
        {'email': patient_user.email, 'code': raw},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    patient_user.refresh_from_db()
    assert patient_user.check_password('old-pass-123!')


@pytest.mark.django_db
def test_password_reset_request_sends_code(api_client: APIClient, patient_user: object, settings: object) -> None:
    """Sprawdza generowanie i wysyłkę jednorazowego kodu przy żądaniu resetu hasła."""
    # Arrange
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

    # Act
    response = api_client.post(
        '/api/v1/auth/password-reset/request/',
        {'email': patient_user.email, 'client': 'web'},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 1
    body = mail.outbox[0].body
    assert 'kod' in body.lower() or any(ch.isdigit() for ch in body)
    assert patient_user.email in mail.outbox[0].to
    assert EmailCode.objects.filter(
        user=patient_user,
        purpose=EmailCodePurpose.PASSWORD_RESET,
        used_at__isnull=True,
    ).exists()
    assert any(
        part.isdigit() and len(part) == 6
        for part in mail.outbox[0].body.replace('\n', ' ').split()
    )


@pytest.mark.django_db
def test_password_reset_request_email_iexact(api_client: APIClient, patient_user: object, settings: object) -> None:
    """Sprawdza niewrażliwość na wielkość liter w adresie e-mail przy żądaniu resetu hasła."""
    # Arrange
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

    # Act
    response = api_client.post(
        '/api/v1/auth/password-reset/request/',
        {'email': patient_user.email.upper(), 'client': 'web'},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_password_reset_request_unknown_email_no_mail(api_client: APIClient, settings: object) -> None:
    """Sprawdza brak wysyłki wiadomości przy żądaniu resetu dla nieistniejącego e-maila."""
    # Arrange
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

    # Act
    response = api_client.post(
        '/api/v1/auth/password-reset/request/',
        {'email': 'nobody@physiocare.test', 'client': 'web'},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['error']['code'] == 'AUTH_029'
    assert 'Nie mamy konta' in response.data['error']['message']
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_password_reset_request_google_only_account(api_client: APIClient, settings: object) -> None:
    """Sprawdza odrzucanie resetu hasła dla kont zintegrowanych wyłącznie z Google."""
    # Arrange
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    user = User.objects.create_user(
        email='google.only@physiocare.test',
        password=None,
        role='PATIENT',
        first_name='G',
        last_name='Only',
        google_sub='google-sub-reset-1',
        email_verified_at=timezone.now(),
    )

    # Act
    response = api_client.post(
        '/api/v1/auth/password-reset/request/',
        {'email': user.email, 'client': 'mobile'},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error']['code'] == 'AUTH_023'
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_password_reset_verify_success(api_client: APIClient, patient_user: object) -> None:
    """Sprawdza pomyślną weryfikację kodu resetu i wydanie tokena jednorazowego."""
    # Arrange
    raw = issue_email_code(user=patient_user, purpose=EmailCodePurpose.PASSWORD_RESET)

    # Act
    response = api_client.post(
        '/api/v1/auth/password-reset/verify/',
        {'email': patient_user.email, 'code': raw},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.data['reset_token']
    assert EmailCode.objects.filter(
        user=patient_user,
        purpose=EmailCodePurpose.PASSWORD_RESET,
        used_at__isnull=False,
    ).exists()
    assert PasswordResetToken.objects.filter(
        user=patient_user,
        used_at__isnull=True,
    ).exists()


@pytest.mark.django_db
def test_password_reset_confirm_success(api_client: APIClient, patient_user: object) -> None:
    """Sprawdza zmianę hasła za pomocą weryfikowanego tokenu resetowania."""
    # Arrange
    reset_token = issue_password_reset_token(user=patient_user)

    # Act
    response = api_client.post(
        '/api/v1/auth/password-reset/confirm/',
        {
            'reset_token': reset_token,
            'new_password': 'new-pass-456!',
            'new_password_confirm': 'new-pass-456!',
        },
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    patient_user.refresh_from_db()
    assert patient_user.check_password('new-pass-456!')
    assert PasswordResetToken.objects.filter(
        user=patient_user,
        used_at__isnull=False,
    ).exists()


@pytest.mark.django_db
def test_password_reset_full_flow(api_client: APIClient, patient_user: object) -> None:
    """Sprawdza pełny proces resetu hasła od weryfikacji kodu po ustawienie nowego hasła."""
    # Arrange
    raw = issue_email_code(user=patient_user, purpose=EmailCodePurpose.PASSWORD_RESET)

    # Act
    verify = api_client.post(
        '/api/v1/auth/password-reset/verify/',
        {'email': patient_user.email, 'code': raw},
        format='json',
    )
    # Assert
    assert verify.status_code == status.HTTP_200_OK
    reset_token = verify.data['reset_token']

    confirm = api_client.post(
        '/api/v1/auth/password-reset/confirm/',
        {
            'reset_token': reset_token,
            'new_password': 'new-pass-789!',
            'new_password_confirm': 'new-pass-789!',
        },
        format='json',
    )
    assert confirm.status_code == status.HTTP_200_OK
    patient_user.refresh_from_db()
    assert patient_user.check_password('new-pass-789!')


@pytest.mark.django_db
def test_password_reset_confirm_mismatch(api_client: APIClient, patient_user: object) -> None:
    """Sprawdza odrzucenie zmiany hasła w przypadku niezgodności powtórzonego hasła."""
    # Arrange
    reset_token = issue_password_reset_token(user=patient_user)

    # Act
    response = api_client.post(
        '/api/v1/auth/password-reset/confirm/',
        {
            'reset_token': reset_token,
            'new_password': 'new-pass-456!',
            'new_password_confirm': 'other-pass-456!',
        },
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    patient_user.refresh_from_db()
    assert patient_user.check_password('old-pass-123!')


@pytest.mark.django_db
def test_password_reset_template_rendering_and_attachment(api_client: APIClient, patient_user: object, settings: object) -> None:
    """Sprawdza poprawność renderowania szablonu oraz załącznika graficznego w e-mailu resetu hasła."""
    # Arrange
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

    # Act
    response = api_client.post(
        '/api/v1/auth/password-reset/request/',
        {'email': patient_user.email, 'client': 'web'},
        format='json',
    )
    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 1

    email_msg = mail.outbox[0]
    assert email_msg.subject == 'PhysioCare - kod resetu hasła'
    assert 'Test' in email_msg.body

    assert len(email_msg.alternatives) == 1
    html_content, mimetype = email_msg.alternatives[0]
    assert mimetype == 'text/html'
    assert 'Cześć Test' in html_content
    assert 'Kod resetu hasła' in html_content
    assert 'cid:physiocare_logo' in html_content

    assert len(email_msg.attachments) == 1
    attached_img = email_msg.attachments[0]
    assert attached_img.get_filename() in ('sygnet.png', 'logo.png')


