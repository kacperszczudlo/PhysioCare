import logging

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from core.logging_formatters import mask_email_for_logging


class TestEmailMaskingForLogging:
    """Testy maskowania adresów e-mail w logach w celu ochrony prywatności (F-07)."""

    @pytest.mark.parametrize(
        ('raw_email', 'expected_masked'),
        [
            ('jan.kowalski@example.com', 'j***i@example.com'),
            ('admin@physiocare.pl', 'a***n@physiocare.pl'),
            ('ab@domain.com', 'a***@domain.com'),
            ('a@domain.com', 'a***@domain.com'),
            ('', 'anonymous'),
            (None, 'anonymous'),
            ('not-an-email', 'anonymous'),
        ],
    )
    def test_mask_email_for_logging_patterns(self, raw_email: str | None, expected_masked: str) -> None:
        """Weryfikuje poprawne formatowanie maski dla różnych adresów e-mail."""
        assert mask_email_for_logging(raw_email) == expected_masked


@pytest.mark.django_db
def test_login_failure_does_not_leak_raw_email_in_logs(api_client: APIClient, caplog: pytest.LogCaptureFixture) -> None:
    """Sprawdza, że nieudane logowanie loguje zamaskowany adres e-mail zamiast surowego plaintext (F-07)."""
    from django.core.cache import cache

    cache.clear()
    raw_email = 'sensitive.patient@example.com'
    try:
        with caplog.at_level(logging.INFO, logger='physiocare.auth'):
            response = api_client.post(
                '/api/v1/auth/login/',
                data={'email': raw_email, 'password': 'WrongPassword123!'},
                format='json',
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        # Logi NIE mogą zawierać pełnego adresu w plaintext
        assert raw_email not in caplog.text
        # Logi MUSZĄ zawierać wersję zredagowaną
        assert 's***t@example.com' in caplog.text
    finally:
        cache.clear()
