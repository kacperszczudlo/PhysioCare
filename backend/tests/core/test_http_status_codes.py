import pytest
from rest_framework import status
from rest_framework.exceptions import (
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)

from core.exceptions import custom_exception_handler


@pytest.mark.django_db
def test_status_200_ok_retrieval(api_client, therapist):
    """Status 200 OK is returned for successful data retrieval requests."""
    api_client.force_authenticate(user=therapist.user)

    response = api_client.get('/api/v1/therapist/profile/')

    assert response.status_code == status.HTTP_200_OK
    assert 'first_name' in response.data or 'id' in response.data or 'email' in response.data


@pytest.mark.django_db
def test_status_201_created_resource(api_client, therapist, patient):
    """Status 201 Created is returned when creating a new resource via POST."""
    api_client.force_authenticate(user=therapist.user)
    payload = {
        'title': 'Rehabilitacja kolana po rekonstrukcji ACL',
        'icd10_code': 'M23.2',
        'status': 'IN_PROGRESS',
    }

    response = api_client.post(
        f'/api/v1/patients/{patient.id}/episodes/',
        data=payload,
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert 'id' in response.data


@pytest.mark.django_db
def test_status_204_no_content_deletion(api_client, patient):
    """Status 204 No Content is returned for successful deletion with empty payload."""
    api_client.force_authenticate(user=patient.user)

    response = api_client.delete(
        '/api/v1/me/device-tokens/',
        data={'expo_push_token': 'ExpoPushToken[ValidTokenForTesting123]'},
        format='json',
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b'' or response.data is None


@pytest.mark.django_db
def test_status_400_bad_request_handler():
    """Status 400 Bad Request handles validation errors with standardized JSON structure."""
    exc = ValidationError({'email': ['Podaj prawidłowy adres e-mail.']})
    context = {'request': None, 'view': None}

    response = custom_exception_handler(exc, context)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error']['code'] in ['INVALID', 'VALIDATION_ERROR']
    assert 'email' in response.data['error']['details']


@pytest.mark.django_db
def test_status_401_unauthorized_handler():
    """Status 401 Unauthorized handles unauthenticated / invalid credentials errors."""
    exc = NotAuthenticated('Wymagana jest autoryzacja.')
    context = {'request': None, 'view': None}

    response = custom_exception_handler(exc, context)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['error']['code'] in ['NOT_AUTHENTICATED', 'AUTHENTICATION_FAILED']
    assert response.data['error']['message'] == 'Wymagana jest autoryzacja.'


@pytest.mark.django_db
def test_status_403_forbidden_handler():
    """Status 403 Forbidden handles permission denied errors."""
    exc = PermissionDenied('Nie masz uprawnień do wykonania tej operacji.')
    context = {'request': None, 'view': None}

    response = custom_exception_handler(exc, context)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['error']['code'] == 'PERMISSION_DENIED'
    assert response.data['error']['message'] == 'Nie masz uprawnień do wykonania tej operacji.'


@pytest.mark.django_db
def test_status_404_not_found_handler():
    """Status 404 Not Found handles missing resources and BOLA boundary violations."""
    exc = NotFound('Zasób nie został odnaleziony.')
    context = {'request': None, 'view': None}

    response = custom_exception_handler(exc, context)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['error']['code'] == 'NOT_FOUND'
    assert response.data['error']['message'] == 'Zasób nie został odnaleziony.'


@pytest.mark.django_db
def test_status_500_server_error_handler():
    """Status 500 Internal Server Error handles unhandled exceptions safely."""
    exc = RuntimeError('Unexpected database breakdown')
    context = {'request': None, 'view': None}

    response = custom_exception_handler(exc, context)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.data['error']['code'] == 'SERVER_ERROR'
    assert 'nieoczekiwany błąd' in response.data['error']['message'].lower()
