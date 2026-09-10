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
def _clear_throttle(settings):
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
def api_client():
    return APIClient()


@pytest.fixture
def therapist(db):
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
def test_patient_register_requires_email_verification(api_client, therapist, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

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

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['needs_email_verification'] is True
    assert 'access' not in response.data
    assert len(mail.outbox) == 1
    user = User.objects.get(email='new.patient@physiocare.test')
    assert user.email_verified_at is None
    assert PatientProfile.objects.filter(user=user).exists()
    assert Consent.objects.filter(user=user, consent_type=ConsentType.TERMS_REQUIRED).exists()


@pytest.mark.django_db
def test_login_blocks_unverified_email(api_client, therapist):
    user = User.objects.create_user(
        email='unverified@physiocare.test',
        password='StrongPass1!',
        role='PATIENT',
        first_name='Ada',
        last_name='Nowak',
        email_verified_at=None,
    )
    PatientProfile.objects.create(user=user, therapist=therapist)

    response = api_client.post(
        '/api/v1/auth/login/',
        {'email': user.email, 'password': 'StrongPass1!'},
        format='json',
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['error']['code'] == 'AUTH_027'


@pytest.mark.django_db
def test_email_verify_issues_tokens(api_client, therapist, settings):
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

    response = api_client.post(
        '/api/v1/auth/email/verify/',
        {'email': user.email, 'code': raw},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert 'user' in response.data
    assert 'access' in response.data
    user.refresh_from_db()
    assert user.email_verified_at is not None


@pytest.mark.django_db
def test_email_resend_sends_new_code(api_client, therapist, settings):
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

    response = api_client.post(
        '/api/v1/auth/email/resend/',
        {'email': user.email},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 1
