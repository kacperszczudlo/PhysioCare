import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory

from core.throttling import LoginRateThrottle, PasswordResetRateThrottle, RegisterRateThrottle


@pytest.mark.django_db
def test_login_rate_throttle_invalid_type() -> None:
    """Sprawdza rzucenie TypeError gdy argument request nie jest prawidłowego typu."""
    # Arrange
    throttle: LoginRateThrottle = LoginRateThrottle()
    # Act
    with pytest.raises(TypeError, match="Argument 'request' musi być instancją Request lub HttpRequest."):
        throttle.get_cache_key(request="invalid_string", view=None)


@pytest.mark.django_db
def test_login_rate_throttle_anonymous() -> None:
    """Sprawdza generowanie klucza cache dla niezalogowanego użytkownika."""
    # Arrange
    factory: APIRequestFactory = APIRequestFactory()
    request: object = factory.post("/api/accounts/login/")
    request.user = AnonymousUser()

    throttle: LoginRateThrottle = LoginRateThrottle()
    cache_key: str | None = throttle.get_cache_key(request=request, view=None)
    # Assert
    assert cache_key is not None
    assert "login" in cache_key


@pytest.mark.django_db
def test_login_rate_throttle_authenticated(patient: object) -> None:
    """Sprawdza zwrócenie None dla zalogowanego użytkownika."""
    # Arrange
    factory: APIRequestFactory = APIRequestFactory()
    request: object = factory.post("/api/accounts/login/")
    request.user = patient.user

    throttle: LoginRateThrottle = LoginRateThrottle()
    # Assert
    assert throttle.get_cache_key(request=request, view=None) is None


@pytest.mark.django_db
def test_register_rate_throttle() -> None:
    """Sprawdza generowanie klucza cache dla rejestracji oraz weryfikację typu."""
    # Arrange
    throttle: RegisterRateThrottle = RegisterRateThrottle()

    # Act
    with pytest.raises(TypeError, match="Argument 'request' musi być instancją Request lub HttpRequest."):
        throttle.get_cache_key(request=12345, view=None)

    factory: RequestFactory = RequestFactory()
    request: object = factory.post("/api/accounts/register/")
    cache_key: str | None = throttle.get_cache_key(request=request, view=None)
    # Assert
    assert cache_key is not None
    assert "register" in cache_key


@pytest.mark.django_db
def test_password_reset_rate_throttle() -> None:
    """Sprawdza generowanie klucza cache dla resetu hasła oraz weryfikację typu."""
    # Arrange
    throttle: PasswordResetRateThrottle = PasswordResetRateThrottle()

    # Act
    with pytest.raises(TypeError, match="Argument 'request' musi być instancją Request lub HttpRequest."):
        throttle.get_cache_key(request=None, view=None)

    factory: RequestFactory = RequestFactory()
    request: object = factory.post("/api/accounts/password-reset/")
    cache_key: str | None = throttle.get_cache_key(request=request, view=None)
    # Assert
    assert cache_key is not None
    assert "password_reset" in cache_key

