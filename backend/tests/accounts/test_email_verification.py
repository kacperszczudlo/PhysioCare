import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.email_codes import issue_email_code
from accounts.models import EmailCodePurpose
from patients.models import PatientProfile
from privacy.models import Consent, ConsentType
from therapists.models import TherapistProfile

User = get_user_model()


@pytest.fixture(autouse=True)
def _clear_throttle(settings: object) -> object:
    """Czyści limity zapytania throttle przed i po każdym teście."""
    cache.clear()
    rates = settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']
    previous = {key: rates.get(key) for key in ('login', 'register', 'password_reset')}
    rates['login'] = '1000/minute'
    rates['register'] = '1000/minute'
    rates['password_reset'] = '1000/minute'
    yield
    for key, value in previous.items():
        if value is not None:
            rates[key] = value
    cache.clear()


@pytest.fixture
def api_client() -> APIClient:
    """Fixture klienta API REST."""
    return APIClient()


@pytest.fixture
def therapist(db: object) -> TherapistProfile:
    """Fixture profilu fizjoterapeuty do testów weryfikacji e-mail."""
    user = User.objects.create_user(
        email='otp.therapist@physiocare.test',
        password='TestPass1!',
        role='THERAPIST',
        first_name='Jan',
        last_name='Kowalski',
        email_verified_at=timezone.now(),
    )
    return TherapistProfile.objects.create(user=user, pwzf_number='81239')


@pytest.mark.django_db
def test_patient_register_requires_email_verification(api_client: APIClient, therapist: TherapistProfile, settings: object) -> None:
    """Sprawdza, czy rejestracja pacjenta wymaga weryfikacji adresu e-mail."""
    # Arrange
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

    # Act
    response = api_client.post(
        '/api/v1/auth/register/patient/',
        {
            'email': 'new.patient@physiocare.test',
            'password': 'StrongPass1!',
            'first_name': 'Ada',
            'last_name': 'Nowak',
            'therapist_id': str(therapist.id),
            'consents': {'terms': True, 'medical_data': True},
        },
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['needs_email_verification'] is True
    assert 'access' not in response.data
    assert len(mail.outbox) == 1
    user = User.objects.get(email='new.patient@physiocare.test')
    assert user.email_verified_at is None
    assert PatientProfile.objects.filter(user=user).exists()
    assert Consent.objects.filter(user=user, consent_type=ConsentType.TERMS_REQUIRED).exists()


@pytest.mark.django_db
def test_login_blocks_unverified_email(api_client: APIClient, therapist: TherapistProfile) -> None:
    """Sprawdza, czy logowanie jest blokowane dla niezweryfikowanego e-maila."""
    # Arrange
    user = User.objects.create_user(
        email='unverified@physiocare.test',
        password='StrongPass1!',
        role='PATIENT',
        first_name='Ada',
        last_name='Nowak',
        email_verified_at=None,
    )
    PatientProfile.objects.create(user=user, therapist=therapist)

    # Act
    response = api_client.post(
        '/api/v1/auth/login/',
        {'email': user.email, 'password': 'StrongPass1!'},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['error']['code'] == 'AUTH_027'


@pytest.mark.django_db
def test_email_verify_issues_tokens(api_client: APIClient, therapist: TherapistProfile, settings: object) -> None:
    """Sprawdza, czy weryfikacja kodu e-mail aktywuje konto i wydaje tokeny JWT."""
    # Arrange
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    user = User.objects.create_user(
        email='verify.me@physiocare.test',
        password='StrongPass1!',
        role='PATIENT',
        first_name='Ada',
        last_name='Nowak',
        email_verified_at=None,
    )
    PatientProfile.objects.create(user=user, therapist=therapist)
    raw = issue_email_code(user=user, purpose=EmailCodePurpose.VERIFY_EMAIL)

    # Act
    response = api_client.post(
        '/api/v1/auth/email/verify/',
        {'email': user.email, 'code': raw},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert 'user' in response.data
    assert 'access' in response.data
    user.refresh_from_db()
    assert user.email_verified_at is not None


@pytest.mark.django_db
def test_email_resend_sends_new_code(api_client: APIClient, therapist: TherapistProfile, settings: object) -> None:
    """Sprawdza, czy ponowne wysłanie kodu e-mail generuje nową wiadomość."""
    # Arrange
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    user = User.objects.create_user(
        email='resend.me@physiocare.test',
        password='StrongPass1!',
        role='PATIENT',
        first_name='Ada',
        last_name='Nowak',
        email_verified_at=None,
    )
    PatientProfile.objects.create(user=user, therapist=therapist)

    # Act
    response = api_client.post(
        '/api/v1/auth/email/resend/',
        {'email': user.email},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_email_verify_template_rendering_and_attachment(api_client: APIClient, therapist: TherapistProfile, settings: object) -> None:
    """Sprawdza renderowanie szablonu wiadomości e-mail oraz załączniki graficzne."""
    # Arrange
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    user = User.objects.create_user(
        email='template.test@physiocare.test',
        password='StrongPass1!',
        role='PATIENT',
        first_name='Leszek',
        last_name='Kowalski',
        email_verified_at=None,
    )
    PatientProfile.objects.create(user=user, therapist=therapist)

    # Act
    response = api_client.post(
        '/api/v1/auth/email/resend/',
        {'email': user.email},
        format='json',
    )
    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 1

    email_msg = mail.outbox[0]
    assert email_msg.subject == 'PhysioCare - potwierdź adres e-mail'
    assert 'Leszek' in email_msg.body
    assert 'PhysioCare' in email_msg.body

    assert len(email_msg.alternatives) == 1
    html_content, mimetype = email_msg.alternatives[0]
    assert mimetype == 'text/html'
    assert 'Cześć Leszek' in html_content
    assert 'Kod weryfikacyjny PhysioCare' in html_content
    assert 'data:image/png;base64,' in html_content
    assert 'Kod jest ważny przez' in html_content

    assert len(email_msg.attachments) == 0


@pytest.mark.django_db
def test_therapist_email_verify_requires_mfa_setup_and_allows_direct_totp_setup(
    api_client: APIClient, settings: object
) -> None:
    """Sprawdza, że po weryfikacji e-mail terapeuta musi skonfigurować MFA i nie dostaje sesji."""
    import pyotp

    from accounts.models import UserMFA

    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    user = User.objects.create_user(
        email='therapist.mfa@physiocare.test',
        password='StrongPass1!',
        role='THERAPIST',
        first_name='Marek',
        last_name='Zieliński',
        email_verified_at=None,
    )
    TherapistProfile.objects.create(user=user, pwzf_number='99881')
    raw_code = issue_email_code(user=user, purpose=EmailCodePurpose.VERIFY_EMAIL)

    verify_resp = api_client.post(
        '/api/v1/auth/email/verify/',
        {'email': user.email, 'code': raw_code},
        format='json',
    )

    assert verify_resp.status_code == status.HTTP_200_OK
    assert verify_resp.data.get('mfa_setup_required') is True
    assert 'mfa_setup_token' in verify_resp.data
    assert 'access' not in verify_resp.data
    assert not api_client.cookies.get('access_token')

    user.refresh_from_db()
    assert user.email_verified_at is not None

    setup_token = verify_resp.data['mfa_setup_token']
    setup_resp = api_client.post(
        '/api/v1/auth/2fa/setup/',
        {'mfa_setup_token': setup_token},
        format='json',
    )
    assert setup_resp.status_code == status.HTTP_200_OK
    secret = setup_resp.data['secret_key']

    enable_resp = api_client.post(
        '/api/v1/auth/2fa/enable/',
        {'mfa_setup_token': setup_token, 'code': pyotp.TOTP(secret).now()},
        format='json',
    )
    assert enable_resp.status_code == status.HTTP_200_OK
    assert UserMFA.objects.get(user=user).is_enabled is True


