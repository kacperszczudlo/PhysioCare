from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from accounts.google_auth import GoogleAuthError, GoogleIdentity


@pytest.fixture(autouse=True)
def _raise_login_throttle(settings: object) -> object:
    """Czyszczenie i podnoszenie limitów zapytania throttle dla testów logowania Google."""
    rates = settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']
    previous = {key: rates.get(key) for key in ('login', 'register', 'password_reset')}
    rates['login'] = '1000/minute'
    rates['register'] = '1000/minute'
    rates['password_reset'] = '1000/minute'
    yield
    for key, value in previous.items():
        if value is not None:
            rates[key] = value


def _google_url() -> str:
    """Zwraca URL punktu końcowego logowania Google."""
    return reverse('login-google')


@pytest.mark.django_db
def test_google_login_not_configured_returns_503(api_client: object, settings: object) -> None:
    """Sprawdza, czy brak konfiguracji Google Client ID zwraca kod 503."""
    # Arrange
    settings.GOOGLE_CLIENT_IDS = []
    # Act
    response = api_client.post(_google_url(), {'credential': 'token'}, format='json')
    # Assert
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.data['error']['code'] == 'AUTH_020'


@pytest.mark.django_db
def test_google_login_missing_credential_returns_400(api_client: object, settings: object) -> None:
    """Sprawdza, czy brak danych uwierzytelniających Google zwraca kod 400."""
    # Arrange
    settings.GOOGLE_CLIENT_IDS = ['test-client-id.apps.googleusercontent.com']
    # Act
    response = api_client.post(_google_url(), {}, format='json')
    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error']['code'] == 'AUTH_021'


@pytest.mark.django_db
def test_google_login_links_existing_email_and_issues_tokens(api_client: object, patient: object, settings: object) -> None:
    """Sprawdza łączenie istniejącego konta po e-mailu i wydawanie tokenów JWT."""
    # Arrange
    settings.GOOGLE_CLIENT_IDS = ['test-client-id.apps.googleusercontent.com']
    identity = GoogleIdentity(
        sub='google-sub-patient-1',
        email=patient.user.email,
        email_verified=True,
        given_name='Pacjent',
        family_name='Testowy',
    )

    # Act
    with patch('accounts.views.verify_google_id_token', return_value=identity):
        response = api_client.post(
            _google_url(),
            {'credential': 'fake-id-token'},
            format='json',
        )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.data['user']['email'] == patient.user.email
    assert 'access' in response.data
    assert 'refresh' in response.data
    patient.user.refresh_from_db()
    assert patient.user.google_sub == 'google-sub-patient-1'


@pytest.mark.django_db
def test_google_login_cookie_delivery_omits_body_tokens(api_client: object, therapist: object, settings: object) -> None:
    """Sprawdza przesyłanie tokenów w ciasteczkach HTTP-only przy logowaniu Google."""
    # Arrange
    settings.GOOGLE_CLIENT_IDS = ['test-client-id.apps.googleusercontent.com']
    therapist.user.google_sub = 'google-sub-therapist-1'
    therapist.user.save(update_fields=['google_sub'])
    identity = GoogleIdentity(
        sub='google-sub-therapist-1',
        email=therapist.user.email,
        email_verified=True,
        given_name='Jan',
        family_name='Kowalski',
    )

    # Act
    with patch('accounts.views.verify_google_id_token', return_value=identity):
        response = api_client.post(
            _google_url(),
            {'credential': 'fake-id-token', 'token_delivery': 'cookie'},
            format='json',
        )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert 'access' not in response.data
    assert 'refresh' not in response.data
    assert 'access_token' in response.cookies
    assert 'refresh_token' in response.cookies


@pytest.mark.django_db
def test_google_login_unknown_account_returns_404(api_client: object, settings: object) -> None:
    """Sprawdza, czy próba logowania nieznanym kontem Google zwraca kod 404."""
    # Arrange
    settings.GOOGLE_CLIENT_IDS = ['test-client-id.apps.googleusercontent.com']
    identity = GoogleIdentity(
        sub='google-sub-unknown',
        email='unknown@physiocare.test',
        email_verified=True,
        given_name='Nowy',
        family_name='User',
    )

    # Act
    with patch('accounts.views.verify_google_id_token', return_value=identity):
        response = api_client.post(
            _google_url(),
            {'id_token': 'fake-id-token'},
            format='json',
        )

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['error']['code'] == 'AUTH_025'
    assert response.data['error']['details']['needs_registration'] is True
    assert response.data['error']['details']['email'] == 'unknown@physiocare.test'


@pytest.mark.django_db
def test_google_login_invalid_token_maps_error(api_client: object, settings: object) -> None:
    """Sprawdza mapowanie błędów przy nieprawidłowym tokenie Google."""
    # Arrange
    settings.GOOGLE_CLIENT_IDS = ['test-client-id.apps.googleusercontent.com']

    # Act
    with patch(
        'accounts.views.verify_google_id_token',
        side_effect=GoogleAuthError('AUTH_022', 'Nie udało się zweryfikować logowania Google.'),
    ):
        response = api_client.post(
            _google_url(),
            {'credential': 'bad-token'},
            format='json',
        )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['error']['code'] == 'AUTH_022'


@pytest.mark.django_db
def test_password_login_hints_google_only_account(api_client: object, patient: object) -> None:
    """Sprawdza podpowiedź przy próbie logowania hasłem dla konta zintegrowanego z Google."""
    # Arrange
    patient.user.google_sub = 'google-sub-only'
    patient.user.set_unusable_password()
    patient.user.save(update_fields=['google_sub', 'password'])

    # Act
    response = api_client.post(
        reverse('login'),
        {'email': patient.user.email, 'password': 'Anything1!'},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['error']['code'] == 'AUTH_023'


@pytest.mark.django_db
def test_therapist_register_with_google_credential(api_client: object, settings: object) -> None:
    """Sprawdza rejestrację fizjoterapeuty za pomocą konta Google."""
    # Arrange
    settings.GOOGLE_CLIENT_IDS = ['test-client-id.apps.googleusercontent.com']
    identity = GoogleIdentity(
        sub='google-sub-new-therapist',
        email='google.therapist@physiocare.test',
        email_verified=True,
        given_name='Anna',
        family_name='Google',
    )

    # Act
    with patch('accounts.serializers.verify_google_id_token', return_value=identity):
        response = api_client.post(
            reverse('register-therapist'),
            {
                'google_credential': 'fake-id-token',
                'pwzf_number': '71299',
                'pwzf_declaration': True,
                'token_delivery': 'cookie',
            },
            format='json',
        )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['user']['email'] == identity.email
    assert response.data['user']['role'] == 'THERAPIST'
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.get(email=identity.email)
    assert user.google_sub == identity.sub
    assert not user.has_usable_password()


@pytest.mark.django_db
def test_patient_register_with_google_credential(api_client: object, therapist: object, settings: object) -> None:
    """Sprawdza rejestrację pacjenta za pomocą konta Google."""
    # Arrange
    settings.GOOGLE_CLIENT_IDS = ['test-client-id.apps.googleusercontent.com']
    identity = GoogleIdentity(
        sub='google-sub-new-patient',
        email='google.patient@physiocare.test',
        email_verified=True,
        given_name='Piotr',
        family_name='Google',
    )

    # Act
    with patch('accounts.serializers.verify_google_id_token', return_value=identity):
        response = api_client.post(
            reverse('register-patient'),
            {
                'google_credential': 'fake-id-token',
                'therapist_id': str(therapist.id),
                'consents': {'terms': True, 'medical_data': True},
            },
            format='json',
        )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['user']['email'] == identity.email
    assert response.data['user']['role'] == 'PATIENT'


@pytest.mark.django_db
def test_google_register_rejects_missing_names(api_client: object, therapist: object, settings: object) -> None:
    """Sprawdza odrzucenie rejestracji Google w przypadku braku imienia i nazwiska."""
    # Arrange
    settings.GOOGLE_CLIENT_IDS = ['test-client-id.apps.googleusercontent.com']
    identity = GoogleIdentity(
        sub='google-sub-no-names',
        email='google.noname@physiocare.test',
        email_verified=True,
        given_name='',
        family_name='',
    )

    # Act
    with patch('accounts.serializers.verify_google_id_token', return_value=identity):
        therapist_response = api_client.post(
            reverse('register-therapist'),
            {
                'google_credential': 'fake-id-token',
                'pwzf_number': '71299',
                'pwzf_declaration': True,
                'token_delivery': 'cookie',
            },
            format='json',
        )
        patient_response = api_client.post(
            reverse('register-patient'),
            {
                'google_credential': 'fake-id-token',
                'therapist_id': str(therapist.id),
                'consents': {'terms': True, 'medical_data': True},
            },
            format='json',
        )

    # Assert
    assert therapist_response.status_code == status.HTTP_400_BAD_REQUEST
    therapist_details = therapist_response.data['error']['details']
    assert 'first_name' in therapist_details or 'last_name' in therapist_details
    assert patient_response.status_code == status.HTTP_400_BAD_REQUEST
    patient_details = patient_response.data['error']['details']
    assert 'first_name' in patient_details or 'last_name' in patient_details


@pytest.mark.django_db
def test_google_register_accepts_names_from_payload(api_client: object, therapist: object, settings: object) -> None:
    """Sprawdza akceptację imienia i nazwiska podanych w payloadzie przy braku w Google."""
    # Arrange
    settings.GOOGLE_CLIENT_IDS = ['test-client-id.apps.googleusercontent.com']
    identity = GoogleIdentity(
        sub='google-sub-payload-names',
        email='google.payload@physiocare.test',
        email_verified=True,
        given_name='',
        family_name='',
    )

    # Act
    with patch('accounts.serializers.verify_google_id_token', return_value=identity):
        response = api_client.post(
            reverse('register-patient'),
            {
                'google_credential': 'fake-id-token',
                'first_name': 'Kasia',
                'last_name': 'Nowak',
                'therapist_id': str(therapist.id),
                'consents': {'terms': True, 'medical_data': True},
            },
            format='json',
        )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['user']['first_name'] == 'Kasia'
    assert response.data['user']['last_name'] == 'Nowak'


@pytest.mark.django_db
def test_google_register_rejects_existing_email(api_client: object, patient: object, therapist: object, settings: object) -> None:
    """Sprawdza odrzucenie rejestracji Google dla istniejącego w bazie adresu e-mail."""
    # Arrange
    settings.GOOGLE_CLIENT_IDS = ['test-client-id.apps.googleusercontent.com']
    identity = GoogleIdentity(
        sub='google-sub-existing-email',
        email=patient.user.email,
        email_verified=True,
        given_name='Jan',
        family_name='Kowalski',
    )

    # Act
    with patch('accounts.serializers.verify_google_id_token', return_value=identity):
        patient_response = api_client.post(
            reverse('register-patient'),
            {
                'google_credential': 'fake-id-token',
                'first_name': 'Jan',
                'last_name': 'Kowalski',
                'therapist_id': str(therapist.id),
                'consents': {'terms': True, 'medical_data': True},
            },
            format='json',
        )
        therapist_response = api_client.post(
            reverse('register-therapist'),
            {
                'google_credential': 'fake-id-token',
                'first_name': 'Jan',
                'last_name': 'Kowalski',
                'pwzf_number': '81234',
                'pwzf_declaration': True,
                'token_delivery': 'cookie',
            },
            format='json',
        )

    # Assert
    assert patient_response.status_code == status.HTTP_400_BAD_REQUEST
    patient_details = patient_response.data['error']['details']
    assert 'email' in patient_details
    assert 'zarejestrowany' in patient_details['email'][0].lower()

    assert therapist_response.status_code == status.HTTP_400_BAD_REQUEST
    therapist_details = therapist_response.data['error']['details']
    assert 'email' in therapist_details
    assert 'zarejestrowany' in therapist_details['email'][0].lower()

