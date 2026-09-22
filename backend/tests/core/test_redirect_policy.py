import pytest

from core.redirect_policy import is_safe_redirect_url


@pytest.mark.django_db
class TestRedirectPolicy:
    """Zbiór testów weryfikujących politykę bezpiecznych przekierowań URL (Open Redirect)."""

    def test_safe_relative_urls_pass(self) -> None:
        """Sprawdza, czy względne adresy URL są uznawane za bezpieczne."""
        # Assert
        assert is_safe_redirect_url('/') is True
        assert is_safe_redirect_url('/dashboard') is True
        assert is_safe_redirect_url('/auth/verify-email?email=user%40example.com') is True

    def test_allowed_frontend_urls_pass(self) -> None:
        """Sprawdza, czy dozwolone adresy domeny frontendowej są uznawane za bezpieczne."""
        # Assert
        assert is_safe_redirect_url('http://localhost:5173/login') is True
        assert is_safe_redirect_url('http://localhost:8081/register') is True

    def test_unsafe_external_domains_rejected(self) -> None:
        """Sprawdza, czy niebezpieczne zewnętrzne domeny są odrzucane."""
        # Assert
        assert is_safe_redirect_url('https://evil-phishing.com') is False
        assert is_safe_redirect_url('http://attacker.com/malware') is False

    def test_protocol_relative_urls_rejected(self) -> None:
        """Sprawdza, czy adresy względne względem protokołu (//domain) są odrzucane."""
        # Assert
        assert is_safe_redirect_url('//evil-phishing.com') is False
        assert is_safe_redirect_url('//attacker.com/path') is False

    def test_javascript_and_invalid_schemes_rejected(self) -> None:
        """Sprawdza, czy niebezpieczne schematy (javascript:, data:) oraz wartości puste są odrzucane."""
        # Assert
        assert is_safe_redirect_url('javascript:alert(1)') is False
        assert is_safe_redirect_url('data:text/html,<script>alert(1)</script>') is False
        assert is_safe_redirect_url(None) is False
        assert is_safe_redirect_url('') is False

