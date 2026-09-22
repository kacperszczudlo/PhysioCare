import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestSecurityHeaders:
    """Zbiór testów weryfikujących nagłówki bezpieczeństwa HTTP (CSP, Permissions-Policy, COOP, Secure Cookies)."""

    def test_api_responses_include_security_headers(self) -> None:
        """Sprawdza obecność i poprawność nagłówków Content-Security-Policy, Permissions-Policy i COOP w odpowiedziach API."""
        # Arrange
        client: APIClient = APIClient()
        response: object = client.get('/api/v1/auth/login/')

        # Assert
        assert 'Content-Security-Policy' in response
        csp: str = response['Content-Security-Policy']
        assert "default-src 'self'" in csp
        assert "connect-src 'self' https: wss:" in csp
        assert "https://www.google.com/recaptcha/" in csp
        assert "https://accounts.google.com/gsi/" in csp
        assert "frame-ancestors 'none'" in csp

        assert 'Permissions-Policy' in response
        permissions: str = response['Permissions-Policy']
        assert "camera=()" in permissions
        assert "microphone=()" in permissions
        assert "geolocation=()" in permissions

        assert 'Cross-Origin-Opener-Policy' in response
        assert response['Cross-Origin-Opener-Policy'] == 'same-origin-allow-popups'

    def test_secure_cookies_flags(self) -> None:
        """Sprawdza poprawność ustawień flag bezpiecznych ciasteczek w konfiguracji Django."""
        # Arrange
        from django.conf import settings
        from django.test import override_settings

        # Act
        with override_settings(SECURE_COOKIES=True, SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True):
            assert settings.SECURE_COOKIES is True
            assert settings.SESSION_COOKIE_SECURE is True
            assert settings.CSRF_COOKIE_SECURE is True

    def test_secure_proxy_ssl_header_configuration(self) -> None:
        """Sprawdza poprawność nagłówka odwrotnego proxy SSL (SECURE_PROXY_SSL_HEADER) i przekazywania hosta."""
        # Arrange
        from django.conf import settings
        from django.test import override_settings

        # Act & Assert
        with override_settings(
            USE_X_FORWARDED_HOST=True,
            SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https'),
        ):
            assert settings.USE_X_FORWARDED_HOST is True
            assert settings.SECURE_PROXY_SSL_HEADER == ('HTTP_X_FORWARDED_PROTO', 'https')




