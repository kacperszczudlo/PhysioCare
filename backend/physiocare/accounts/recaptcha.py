import logging

import requests
from django.conf import settings
from rest_framework import serializers

logger = logging.getLogger('physiocare.auth')

VERIFY_URL: str = 'https://www.google.com/recaptcha/api/siteverify'


def verify_recaptcha_token(
    token: str | None,
    remote_ip: str | None = None,
    client: str | None = None,
) -> None:
    """Weryfikuje token Google reCAPTCHA v2/v3 w API siteverify Google.

    Jeśli flaga RECAPTCHA_ENABLED wynosi False lub klucz prywatny jest pusty, pomija weryfikację.

    Args:
        token (str | None): Token przesłany z formularza.
        remote_ip (str | None): Opcjonalny adres IP klienta.

    Raises:
        serializers.ValidationError: Gdy weryfikacja reCAPTCHA niepowiedzie się lub wynik zaufania jest za niski.
    """
    recaptcha_enabled = settings.RECAPTCHA_ENABLED if hasattr(settings, 'RECAPTCHA_ENABLED') else False
    if not recaptcha_enabled:
        return

    legacy_secret = getattr(settings, 'RECAPTCHA_SECRET_KEY', '').strip()
    if client == 'web':
        secret_key = getattr(settings, 'RECAPTCHA_V3_SECRET_KEY', '').strip()
    elif client == 'mobile':
        secret_key = getattr(settings, 'RECAPTCHA_V2_SECRET_KEY', '').strip()
    elif legacy_secret:
        secret_key = legacy_secret
    else:
        raise serializers.ValidationError(
            'Weryfikacja CAPTCHA nie jest poprawnie skonfigurowana.'
        )
    if not secret_key:
        return

    if not token or not isinstance(token, str) or not token.strip():
        raise serializers.ValidationError(
            'Weryfikacja CAPTCHA jest wymagana. Potwierdź, że nie jesteś botem.'
        )

    payload = {
        'secret': secret_key,
        'response': token.strip(),
    }
    if remote_ip and isinstance(remote_ip, str):
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
    threshold_val = settings.RECAPTCHA_SCORE_THRESHOLD if hasattr(settings, 'RECAPTCHA_SCORE_THRESHOLD') else 0.5
    threshold = float(threshold_val)

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
