from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings
from rest_framework import serializers

from accounts.recaptcha import verify_recaptcha_token


@pytest.mark.django_db
class TestRecaptchaVerification:
    @override_settings(RECAPTCHA_ENABLED=False, RECAPTCHA_SECRET_KEY='')
    def test_disabled_recaptcha_bypasses_validation(self):
        # Should not raise any error even with None or empty token
        verify_recaptcha_token(None)
        verify_recaptcha_token('')
        verify_recaptcha_token('dummy-token')

    @override_settings(RECAPTCHA_ENABLED=True, RECAPTCHA_SECRET_KEY='secret_key_test')
    def test_missing_token_raises_validation_error(self):
        with pytest.raises(serializers.ValidationError) as exc_info:
            verify_recaptcha_token(None)
        assert 'Weryfikacja CAPTCHA jest wymagana' in str(exc_info.value)

        with pytest.raises(serializers.ValidationError) as exc_info:
            verify_recaptcha_token('  ')
        assert 'Weryfikacja CAPTCHA jest wymagana' in str(exc_info.value)

    @override_settings(RECAPTCHA_ENABLED=True, RECAPTCHA_SECRET_KEY='secret_key_test')
    @patch('accounts.recaptcha.requests.post')
    def test_successful_recaptcha_verification(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'score': 0.9,
        }
        mock_post.return_value = mock_response

        verify_recaptcha_token('valid_token_123')
        mock_post.assert_called_once()
        assert mock_post.call_args[1]['data']['response'] == 'valid_token_123'
        assert mock_post.call_args[1]['data']['secret'] == 'secret_key_test'

    @override_settings(RECAPTCHA_ENABLED=True, RECAPTCHA_SECRET_KEY='secret_key_test')
    @patch('accounts.recaptcha.requests.post')
    def test_failed_recaptcha_verification(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': False,
            'error-codes': ['invalid-input-response'],
        }
        mock_post.return_value = mock_response

        with pytest.raises(serializers.ValidationError) as exc_info:
            verify_recaptcha_token('invalid_token')
        assert 'nie powiodła się' in str(exc_info.value)

    @override_settings(
        RECAPTCHA_ENABLED=True,
        RECAPTCHA_SECRET_KEY='secret_key_test',
        RECAPTCHA_SCORE_THRESHOLD=0.7,
    )
    @patch('accounts.recaptcha.requests.post')
    def test_low_score_recaptcha_fails(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'score': 0.3,
        }
        mock_post.return_value = mock_response

        with pytest.raises(serializers.ValidationError) as exc_info:
            verify_recaptcha_token('low_score_token')
        assert 'niski wynik zaufania' in str(exc_info.value)
