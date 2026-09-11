import pytest

from core.redirect_policy import is_safe_redirect_url


@pytest.mark.django_db
class TestRedirectPolicy:
    def test_safe_relative_urls_pass(self):
        assert is_safe_redirect_url('/') is True
        assert is_safe_redirect_url('/dashboard') is True
        assert is_safe_redirect_url('/auth/verify-email?email=user%40example.com') is True

    def test_allowed_frontend_urls_pass(self):
        assert is_safe_redirect_url('http://localhost:5173/login') is True
        assert is_safe_redirect_url('http://localhost:8081/register') is True

    def test_unsafe_external_domains_rejected(self):
        assert is_safe_redirect_url('https://evil-phishing.com') is False
        assert is_safe_redirect_url('http://attacker.com/malware') is False

    def test_protocol_relative_urls_rejected(self):
        assert is_safe_redirect_url('//evil-phishing.com') is False
        assert is_safe_redirect_url('//attacker.com/path') is False

    def test_javascript_and_invalid_schemes_rejected(self):
        assert is_safe_redirect_url('javascript:alert(1)') is False
        assert is_safe_redirect_url('data:text/html,<script>alert(1)</script>') is False
        assert is_safe_redirect_url(None) is False
        assert is_safe_redirect_url('') is False
