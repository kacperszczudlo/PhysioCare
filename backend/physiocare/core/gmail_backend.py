from __future__ import annotations

import base64
import logging
import time
from collections.abc import Sequence
from typing import Any

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMessage

logger = logging.getLogger('physiocare.api')


class GmailEmailBackend(BaseEmailBackend):
    """Backend pocztowy Django wysyłający wiadomości e-mail przez Gmail REST API.

    Umożliwia niezawodną wysyłkę e-maili przez port HTTPS 443 w środowiskach
    chmurowych (np. darmowy tier Render), gdzie porty SMTP (25, 465, 587)
    są zablokowane na poziomie zapory sieciowej.

    Obsługuje automatyczne odświeżanie tokena OAuth2, buforowanie czasu
    ważności tokena w pamięci oraz ponawianie wysyłki w przypadku kodu 401.
    """

    TOKEN_URL: str = 'https://oauth2.googleapis.com/token'
    SEND_URL: str = 'https://gmail.googleapis.com/gmail/v1/users/me/messages/send'

    _access_token: str | None = None
    _token_expiry: float = 0.0

    def __init__(
        self,
        fail_silently: bool = False,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Inicjalizuje backend pocztowy Gmail REST API.

        Args:
            fail_silently (bool): Czy ignorować błędy wysyłki bez rzucania wyjątków.
            client_id (str | None): Identyfikator klienta OAuth2 z Google Cloud.
            client_secret (str | None): Klucz tajny klienta OAuth2 z Google Cloud.
            refresh_token (str | None): Długoterminowy token odświeżania OAuth2.
            timeout (int | None): Limit czasu żądań HTTP w sekundach.
            **kwargs (Any): Dodatkowe argumenty przekazywane do klasy bazowej Django.
        """
        super().__init__(fail_silently=fail_silently, **kwargs)

        self.client_id: str = (
            client_id
            if client_id is not None
            else (getattr(settings, 'GMAIL_CLIENT_ID', '') or getattr(settings, 'GOOGLE_CLIENT_ID', ''))
        )
        self.client_secret: str = (
            client_secret
            if client_secret is not None
            else getattr(settings, 'GMAIL_CLIENT_SECRET', '')
        )
        self.refresh_token: str = (
            refresh_token
            if refresh_token is not None
            else getattr(settings, 'GMAIL_REFRESH_TOKEN', '')
        )
        self.timeout: int = (
            timeout
            if timeout is not None
            else int(getattr(settings, 'EMAIL_TIMEOUT', 10))
        )

    def _get_access_token(self) -> str:
        """Pobiera aktywny token dostępowy OAuth2 lub odświeża go przy użyciu refresh tokena.

        Returns:
            str: Ważny token dostępowy Bearer dla Gmail API.

        Raises:
            ImproperlyConfigured: Gdy brakuje wymaganych zmiennych konfiguracyjnych OAuth2.
            RuntimeError: Gdy serwer autoryzacji Google zwróci błąd podczas wymiany tokena.
        """
        now = time.time()
        if self._access_token and now < (self._token_expiry - 60.0):
            return self._access_token

        if not self.client_id or not self.client_secret or not self.refresh_token:
            raise ImproperlyConfigured(
                'Wymagane zmienne GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET oraz GMAIL_REFRESH_TOKEN '
                'muszą być skonfigurowane w pliku konfiguracyjnym lub zmiennych środowiskowych.'
            )

        response = requests.post(
            self.TOKEN_URL,
            data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token',
            },
            timeout=self.timeout,
        )

        if not response.ok:
            error_msg = f'Nie udało się odświeżyć tokena Gmail API ({response.status_code}): {response.text}'
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        data: dict[str, Any] = response.json()
        self._access_token = str(data['access_token'])
        expires_in = float(data.get('expires_in', 3600))
        self._token_expiry = now + expires_in
        return self._access_token

    def send_messages(self, email_messages: Sequence[EmailMessage]) -> int:
        """Wysyła listę wiadomości e-mail za pośrednictwem Gmail REST API.

        Args:
            email_messages (Sequence[EmailMessage]): Kolekcja instancji wiadomości e-mail do wysłania.

        Returns:
            int: Liczba pomyślnie wysłanych wiadomości e-mail.

        Raises:
            RuntimeError: Gdy zapytanie do Gmail API zakończy się błędem (przy fail_silently=False).
            ImproperlyConfigured: Gdy konfiguracja uwierzytelniania jest niekompletna.
        """
        if not email_messages:
            return 0

        sent_count = 0
        try:
            token = self._get_access_token()
        except Exception as exc:
            if not self.fail_silently:
                raise
            logger.exception('Błąd uwierzytelniania Gmail API: %s', exc)
            return 0

        for message in email_messages:
            try:
                raw_bytes = message.message().as_bytes()
                raw_b64 = base64.urlsafe_b64encode(raw_bytes).decode('ascii')

                headers: dict[str, str] = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                }
                res = requests.post(
                    self.SEND_URL,
                    headers=headers,
                    json={'raw': raw_b64},
                    timeout=self.timeout,
                )

                if res.status_code == 401:
                    # Token mógł wygasnąć - czyścimy bufor i ponawiamy zapytanie raz
                    self._access_token = None
                    token = self._get_access_token()
                    headers['Authorization'] = f'Bearer {token}'
                    res = requests.post(
                        self.SEND_URL,
                        headers=headers,
                        json={'raw': raw_b64},
                        timeout=self.timeout,
                    )

                if not res.ok:
                    raise RuntimeError(
                        f'Błąd wysyłki wiadomości Gmail API ({res.status_code}): {res.text}'
                    )

                sent_count += 1
            except Exception as exc:
                if not self.fail_silently:
                    raise
                logger.exception('Błąd wysyłki wiadomości Gmail API: %s', exc)

        return sent_count


# Aliasy zachowujące pełną kompatybilność wsteczną
EmailBackend = GmailEmailBackend
GmailApiEmailBackend = GmailEmailBackend
