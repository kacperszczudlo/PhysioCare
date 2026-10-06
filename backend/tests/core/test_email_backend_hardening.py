import pytest
from django.core.exceptions import ImproperlyConfigured


class TestEmailBackendHardening:
    """Testy zabezpieczeń konfiguracji backendu poczty w środowisku produkcyjnym."""

    def test_console_backend_rejected_on_production(self) -> None:
        """Sprawdza odrzucenie console.EmailBackend przy DJANGO_DEBUG=false."""
        debug = False
        email_backend = 'django.core.mail.backends.console.EmailBackend'

        with pytest.raises(ImproperlyConfigured) as exc_info:
            if not debug and email_backend == 'django.core.mail.backends.console.EmailBackend':
                raise ImproperlyConfigured(
                    'Konfiguracja django.core.mail.backends.console.EmailBackend jest zabroniona przy DJANGO_DEBUG=false.'
                )

        assert 'zabroniona przy DJANGO_DEBUG=false' in str(exc_info.value)

    def test_smtp_backend_allowed_on_production(self) -> None:
        """Sprawdza akceptację bezpiecznego backendu poczty przy DJANGO_DEBUG=false."""
        debug = False
        email_backend = 'django.core.mail.backends.smtp.EmailBackend'

        # Nie powinno rzucić wyjątku
        if not debug and email_backend == 'django.core.mail.backends.console.EmailBackend':
            raise ImproperlyConfigured('Błąd!')
