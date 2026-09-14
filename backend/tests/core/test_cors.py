import pytest
from rest_framework.test import APIClient

from core.redirect_policy import get_allowed_redirect_hosts, is_safe_redirect_url


@pytest.mark.django_db
class TestCorsConfiguration:
    def test_allowed_origin_preflight_options_request(self):
        client = APIClient()
        response = client.options(
            '/api/v1/auth/login/',
            HTTP_ORIGIN='http://localhost:5173',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='x-physiocare-token-delivery, content-type',
        )

        assert response.status_code in (200, 204)
        assert response.headers.get('Access-Control-Allow-Origin') == 'http://localhost:5173'
        assert response.headers.get('Access-Control-Allow-Credentials') == 'true'

        allowed_headers = response.headers.get('Access-Control-Allow-Headers', '').lower()
        assert 'x-physiocare-token-delivery' in allowed_headers
        assert 'content-type' in allowed_headers

        allowed_methods = response.headers.get('Access-Control-Allow-Methods', '')
        assert 'POST' in allowed_methods

    def test_disallowed_origin_request_denied(self):
        client = APIClient()
        response = client.options(
            '/api/v1/auth/login/',
            HTTP_ORIGIN='http://evil-untrusted-domain.com',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
        )

        assert 'Access-Control-Allow-Origin' not in response.headers

    def test_cors_exposed_headers_present(self):
        client = APIClient()
        response = client.get(
            '/api/v1/auth/login/',
            HTTP_ORIGIN='http://localhost:5173',
        )

        assert 'Access-Control-Expose-Headers' in response.headers
        exposed = response.headers.get('Access-Control-Expose-Headers', '').lower()
        assert 'x-request-id' in exposed
        assert 'x-response-time-ms' in exposed
        assert 'content-disposition' in exposed

    def test_custom_allowed_header_x_request_id(self):
        client = APIClient()
        response = client.options(
            '/api/v1/auth/login/',
            HTTP_ORIGIN='http://localhost:5173',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='GET',
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='x-request-id',
        )

        assert response.status_code in (200, 204)
        allowed_headers = response.headers.get('Access-Control-Allow-Headers', '').lower()
        assert 'x-request-id' in allowed_headers

    def test_redirect_policy_uses_cors_allowed_origins(self):
        hosts = get_allowed_redirect_hosts()
        assert 'localhost:5173' in hosts or 'localhost' in hosts
        assert is_safe_redirect_url('http://localhost:5173/auth/callback')
        assert not is_safe_redirect_url('http://evil-phishing-site.com/login')
