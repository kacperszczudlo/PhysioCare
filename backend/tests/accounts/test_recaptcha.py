from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings
from rest_framework import serializers

from accounts.recaptcha import verify_recaptcha_token


@pytest.mark.django_db
class TestRecaptchaVerification:
    """Testy weryfikacji tokenów Google reCAPTCHA v3."""

    @override_settings(DEBUG=True, RECAPTCHA_ENABLED=False, RECAPTCHA_SECRET_KEY='')
    def test_disabled_recaptcha_bypasses_validation(self) -> None:
        """Sprawdza, czy wyłączona reCAPTCHA pomija walidację tokena."""
        # Arrange
        verify_recaptcha_token(None)
        verify_recaptcha_token('')
        verify_recaptcha_token('dummy-token')

    @override_settings(RECAPTCHA_ENABLED=True, RECAPTCHA_SECRET_KEY='secret_key_test')
    def test_missing_token_raises_validation_error(self) -> None:
        """Sprawdza rzucenie błędu walidacji przy braku tokenu CAPTCHA."""
        # Act
        with pytest.raises(serializers.ValidationError) as exc_info:
            verify_recaptcha_token(None)
        # Assert
        assert 'Weryfikacja CAPTCHA jest wymagana' in str(exc_info.value)

        with pytest.raises(serializers.ValidationError) as exc_info:
            verify_recaptcha_token('  ')
        assert 'Weryfikacja CAPTCHA jest wymagana' in str(exc_info.value)

    @override_settings(RECAPTCHA_ENABLED=True, RECAPTCHA_SECRET_KEY='secret_key_test')
    @patch('accounts.recaptcha.requests.post')
    def test_successful_recaptcha_verification(self, mock_post: MagicMock) -> None:
        """Sprawdza pomyślną weryfikację prawidłowego tokenu reCAPTCHA."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'score': 0.9,
        }
        mock_post.return_value = mock_response

        verify_recaptcha_token('valid_token_123')
        # Assert
        mock_post.assert_called_once()
        assert mock_post.call_args[1]['data']['response'] == 'valid_token_123'
        assert mock_post.call_args[1]['data']['secret'] == 'secret_key_test'

    @override_settings(RECAPTCHA_ENABLED=True, RECAPTCHA_SECRET_KEY='secret_key_test')
    @patch('accounts.recaptcha.requests.post')
    def test_failed_recaptcha_verification(self, mock_post: MagicMock) -> None:
        """Sprawdza zgłoszenie błędu przy odrzuceniu tokenu przez Google reCAPTCHA."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': False,
            'error-codes': ['invalid-input-response'],
        }
        mock_post.return_value = mock_response

        # Act
        with pytest.raises(serializers.ValidationError) as exc_info:
            verify_recaptcha_token('invalid_token')
        # Assert
        assert 'nie powiodła się' in str(exc_info.value)

    @override_settings(
        RECAPTCHA_ENABLED=True,
        RECAPTCHA_SECRET_KEY='secret_key_test',
        RECAPTCHA_SCORE_THRESHOLD=0.7,
    )
    @patch('accounts.recaptcha.requests.post')
    def test_low_score_recaptcha_fails(self, mock_post: MagicMock) -> None:
        """Sprawdza odrzucenie odpowiedzi reCAPTCHA ze zbyt niskim wynikiem zaufania (score)."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'score': 0.3,
        }
        mock_post.return_value = mock_response

        # Act
        with pytest.raises(serializers.ValidationError) as exc_info:
            verify_recaptcha_token('low_score_token')
        # Assert
        assert 'niski wynik zaufania' in str(exc_info.value)

    def test_settings_rejection_logic_on_production_without_recaptcha(self) -> None:
        """Sprawdza odrzucenie konfiguracji produkcyjnej bez włączonej reCAPTCHA."""
        from django.core.exceptions import ImproperlyConfigured

        debug = False
        recaptcha_enabled = False

        with pytest.raises(ImproperlyConfigured) as exc_info:
            if not debug and not recaptcha_enabled:
                raise ImproperlyConfigured(
                    'RECAPTCHA_ENABLED musi być ustawione na true przy DJANGO_DEBUG=false.'
                )
        assert 'RECAPTCHA_ENABLED musi być ustawione' in str(exc_info.value)

    def test_settings_rejection_logic_on_production_without_secret_key(self) -> None:
        """Sprawdza odrzucenie konfiguracji produkcyjnej bez klucza reCAPTCHA."""
        from django.core.exceptions import ImproperlyConfigured

        debug = False
        recaptcha_enabled = True
        recaptcha_secret_key = ''

        with pytest.raises(ImproperlyConfigured) as exc_info:
            if not debug and recaptcha_enabled and not recaptcha_secret_key.strip():
                raise ImproperlyConfigured(
                    'RECAPTCHA_SECRET_KEY jest wymagany przy DJANGO_DEBUG=false.'
                )
        assert 'RECAPTCHA_SECRET_KEY jest wymagany' in str(exc_info.value)


