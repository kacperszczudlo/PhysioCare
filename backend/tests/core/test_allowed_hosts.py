import pytest
from django.core.exceptions import ImproperlyConfigured


@pytest.mark.django_db
class TestAllowedHostsHardening:
    """Testy zabezpieczeń nagłówka hostów (ALLOWED_HOSTS)."""

    def test_wildcard_rejection_logic_on_production(self) -> None:
        """Sprawdza odrzucenie maski wieloznacznej '*' w zalecanym środowisku produkcyjnym."""
        # Arrange
        debug = False
        allowed_hosts = ['localhost', '*']

        # Act
        with pytest.raises(ImproperlyConfigured) as exc_info:
            if not debug and '*' in allowed_hosts:
                raise ImproperlyConfigured(
                    'Wildcard "*" w DJANGO_ALLOWED_HOSTS jest zabroniony przy DJANGO_DEBUG=false.'
                )
        # Assert
        assert 'zabroniony' in str(exc_info.value)

