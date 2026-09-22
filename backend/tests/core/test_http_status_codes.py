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
def test_status_200_ok_retrieval(api_client: object, therapist: object) -> None:
    """Sprawdza, czy status 200 OK jest zwracany przy udanym pobraniu danych."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)

    response: object = api_client.get('/api/v1/therapist/profile/')

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert 'first_name' in response.data or 'id' in response.data or 'email' in response.data


@pytest.mark.django_db
def test_status_201_created_resource(api_client: object, therapist: object, patient: object) -> None:
    """Sprawdza, czy status 201 Created jest zwracany przy tworzeniu nowego zasobu metodą POST."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)
    payload: dict[str, str] = {
        'title': 'Rehabilitacja kolana po rekonstrukcji ACL',
        'icd10_code': 'M23.2',
        'status': 'IN_PROGRESS',
    }

    response: object = api_client.post(
        f'/api/v1/patients/{patient.id}/episodes/',
        data=payload,
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert 'id' in response.data


@pytest.mark.django_db
def test_status_204_no_content_deletion(api_client: object, patient: object) -> None:
    """Sprawdza, czy status 204 No Content jest zwracany przy udanym usunięciu zasobu bez treści."""
    # Arrange
    api_client.force_authenticate(user=patient.user)

    response: object = api_client.delete(
        '/api/v1/me/device-tokens/',
        data={'expo_push_token': 'ExpoPushToken[ValidTokenForTesting123]'},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b'' or response.data is None


@pytest.mark.django_db
def test_status_401_unauthorized_via_api_client(api_client: object) -> None:
    """Sprawdza, czy status 401 HTTP jest zwracany przy braku autoryzacji w wywołaniu APIClient."""
    # Arrange
    response: object = api_client.get('/api/v1/therapist/profile/')

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['error']['code'] in ['NOT_AUTHENTICATED', 'AUTHENTICATION_FAILED']
    assert 'error' in response.data


@pytest.mark.django_db
def test_status_404_not_found_via_api_client(api_client: object, therapist: object) -> None:
    """Sprawdza, czy status 404 HTTP jest zwracany przy braku zasobu na trasie DRF."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)
    response: object = api_client.get('/api/v1/patients/00000000-0000-0000-0000-000000000000/episodes/')

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['error']['code'] == 'NOT_FOUND'


@pytest.mark.django_db
def test_status_400_bad_request_handler() -> None:
    """Sprawdza, czy status 400 Bad Request obsługuje błędy walidacji ze standaryzowaną strukturą JSON."""
    # Arrange
    exc: ValidationError = ValidationError({'email': ['Podaj prawidłowy adres e-mail.']})
    context: dict[str, object] = {'request': None, 'view': None}

    response: object = custom_exception_handler(exc, context)

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error']['code'] in ['INVALID', 'VALIDATION_ERROR']
    assert 'email' in response.data['error']['details']


@pytest.mark.django_db
def test_status_401_unauthorized_handler() -> None:
    """Sprawdza, czy status 401 Unauthorized obsługuje błędy braku autoryzacji."""
    # Arrange
    exc: NotAuthenticated = NotAuthenticated('Wymagana jest autoryzacja.')
    context: dict[str, object] = {'request': None, 'view': None}

    response: object = custom_exception_handler(exc, context)

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['error']['code'] in ['NOT_AUTHENTICATED', 'AUTHENTICATION_FAILED']
    assert response.data['error']['message'] == 'Wymagana jest autoryzacja.'


@pytest.mark.django_db
def test_status_403_forbidden_handler() -> None:
    """Sprawdza, czy status 403 Forbidden obsługuje błędy braku uprawnień."""
    # Arrange
    exc: PermissionDenied = PermissionDenied('Nie masz uprawnień do wykonania tej operacji.')
    context: dict[str, object] = {'request': None, 'view': None}

    response: object = custom_exception_handler(exc, context)

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['error']['code'] == 'PERMISSION_DENIED'
    assert response.data['error']['message'] == 'Nie masz uprawnień do wykonania tej operacji.'


@pytest.mark.django_db
def test_status_404_not_found_handler() -> None:
    """Sprawdza, czy status 404 Not Found obsługuje nieznalezione zasoby oraz naruszenia BOLA."""
    # Arrange
    exc: NotFound = NotFound('Zasób nie został odnaleziony.')
    context: dict[str, object] = {'request': None, 'view': None}

    response: object = custom_exception_handler(exc, context)

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data['error']['code'] == 'NOT_FOUND'
    assert response.data['error']['message'] == 'Zasób nie został odnaleziony.'


@pytest.mark.django_db
def test_status_500_server_error_handler() -> None:
    """Sprawdza, czy status 500 Internal Server Error bezpiecznie obsługuje nieobsłużone wyjątki."""
    # Arrange
    exc: RuntimeError = RuntimeError('Unexpected database breakdown')
    context: dict[str, object] = {'request': None, 'view': None}

    response: object = custom_exception_handler(exc, context)

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.data['error']['code'] == 'SERVER_ERROR'
    assert 'nieoczekiwany błąd' in response.data['error']['message'].lower()


