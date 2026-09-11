import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestSecurityHeaders:
    def test_api_responses_include_security_headers(self):
        client = APIClient()
        response = client.get('/api/v1/auth/login/')

        assert 'Content-Security-Policy' in response
        csp = response['Content-Security-Policy']
        assert "default-src 'self'" in csp
        assert "https://www.google.com/recaptcha/" in csp
        assert "https://accounts.google.com/gsi/" in csp
        assert "frame-ancestors 'none'" in csp

        assert 'Permissions-Policy' in response
        permissions = response['Permissions-Policy']
        assert "camera=()" in permissions
        assert "microphone=()" in permissions
        assert "geolocation=()" in permissions

        assert 'Cross-Origin-Opener-Policy' in response
        assert response['Cross-Origin-Opener-Policy'] == 'same-origin-allow-popups'

    def test_secure_cookies_flags(self):
        from django.conf import settings
        from django.test import override_settings

        with override_settings(SECURE_COOKIES=True, SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True):
            assert settings.SECURE_COOKIES is True
            assert settings.SESSION_COOKIE_SECURE is True
            assert settings.CSRF_COOKIE_SECURE is True


