import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status

LOGIN_FAIL_MESSAGE: str = 'Nieprawidłowy e-mail lub hasło.'


@pytest.fixture(autouse=True)
def _clear_login_throttle() -> object:
    """Czyści cache próśb o zalogowanie (throttle)."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
def test_login_unknown_email_returns_generic_message(api_client: object) -> None:
    """Sprawdza, czy nieznany e-mail zwraca ogólny komunikat błędu."""
    # Arrange
    url = reverse('login')
    # Act
    response = api_client.post(
        url,
        {'email': 'brak@example.com', 'password': 'Anything1!'},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['error']['code'] == 'AUTH_001'
    assert response.data['error']['message'] == LOGIN_FAIL_MESSAGE


@pytest.mark.django_db
def test_login_wrong_password_returns_same_generic_message(api_client: object, patient: object) -> None:
    """Sprawdza, czy błędne hasło zwraca taki sam ogólny komunikat błędu jak nieznany e-mail."""
    # Arrange
    url = reverse('login')
    # Act
    response = api_client.post(
        url,
        {'email': patient.user.email, 'password': 'WrongPass1!'},
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['error']['code'] == 'AUTH_001'
    assert response.data['error']['message'] == LOGIN_FAIL_MESSAGE

