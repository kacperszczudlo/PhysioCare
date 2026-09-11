import logging

import requests
from django.conf import settings
from rest_framework import serializers

logger = logging.getLogger('physiocare.auth')

VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'


def verify_recaptcha_token(token: str | None, remote_ip: str | None = None) -> None:
    """
    Verifies a Google reCAPTCHA v2/v3 token against Google siteverify API.
    If RECAPTCHA_ENABLED is False or secret key is empty, bypasses validation (dev/testing).
    Raises serializers.ValidationError if verification fails or score is too low.
    """
    if not getattr(settings, 'RECAPTCHA_ENABLED', False):
        return

    secret_key = getattr(settings, 'RECAPTCHA_SECRET_KEY', '').strip()
    if not secret_key:
        return

    if not token or not str(token).strip():
        raise serializers.ValidationError(
            'Weryfikacja CAPTCHA jest wymagana. Potwierdź, że nie jesteś botem.'
        )

    payload = {
        'secret': secret_key,
        'response': str(token).strip(),
    }
    if remote_ip:
        payload['remoteip'] = remote_ip

    try:
        response = requests.post(VERIFY_URL, data=payload, timeout=5)
        data = response.json()
    except Exception as exc:
        logger.error('Failed to communicate with reCAPTCHA API: %s', exc)
        raise serializers.ValidationError(
            'Błąd połączenia z serwerem weryfikacji CAPTCHA. Spróbuj ponownie.'
        ) from exc

    success = data.get('success', False)
    score = data.get('score')
    threshold = getattr(settings, 'RECAPTCHA_SCORE_THRESHOLD', 0.5)

    if not success:
        error_codes = data.get('error-codes', [])
        logger.warning('reCAPTCHA verification failed: error_codes=%s', error_codes)
        raise serializers.ValidationError(
            'Weryfikacja CAPTCHA nie powiodła się. Spróbuj ponownie.'
        )

    if score is not None and float(score) < threshold:
        logger.warning('reCAPTCHA score too low: score=%s threshold=%s', score, threshold)
        raise serializers.ValidationError(
            'Weryfikacja bota zwróciła niski wynik zaufania. Spróbuj ponownie.'
        )
