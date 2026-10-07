import base64
import logging
import time
from typing import Any

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMessage

logger = logging.getLogger(__name__)


class GmailApiEmailBackend(BaseEmailBackend):
    """Django EmailBackend wysyłający wiadomości e-mail przez oficjalne Gmail REST API (HTTPS port 443).

    Rozwiązuje problem zablokowanych portów SMTP (25, 465, 587) na platformach hostingowych
    takich jak darmowy tier Render lub środowiska chmurowe z restrykcjami sieciowymi.
    """

    TOKEN_URL = "https://oauth2.googleapis.com/token"
    SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

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
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.client_id = (
            client_id
            or getattr(settings, 'GMAIL_CLIENT_ID', '')
            or getattr(settings, 'GOOGLE_CLIENT_ID', '')
        )
        self.client_secret = (
            client_secret
            or getattr(settings, 'GMAIL_CLIENT_SECRET', '')
        )
        self.refresh_token = (
            refresh_token
            or getattr(settings, 'GMAIL_REFRESH_TOKEN', '')
        )
        self.timeout = (
            timeout
            if timeout is not None
            else getattr(settings, 'EMAIL_TIMEOUT', 10)
        )

    def _get_access_token(self) -> str:
        """Pobiera lub odświeża token dostępowy OAuth2 za pomocą refresh tokena."""
        now = time.time()
        if self._access_token and now < (self._token_expiry - 60):
            return self._access_token

        if not self.client_id or not self.client_secret or not self.refresh_token:
            raise ImproperlyConfigured(
                "Wymagane zmienne GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET oraz GMAIL_REFRESH_TOKEN "
                "muszą być skonfigurowane w settings lub zmiennych środowiskowych."
            )

        response = requests.post(
            self.TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=self.timeout,
        )

        if not response.ok:
            error_msg = f"Nie udało się odświeżyć tokena Gmail API ({response.status_code}): {response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        data = response.json()
        self._access_token = data["access_token"]
        expires_in = data.get("expires_in", 3600)
        self._token_expiry = now + float(expires_in)
        return self._access_token

    def send_messages(self, email_messages: list[EmailMessage]) -> int:
        """Wysyła listę wiadomości e-mail za pośrednictwem Gmail REST API."""
        if not email_messages:
            return 0

        sent_count = 0
        try:
            token = self._get_access_token()
        except Exception as exc:
            if not self.fail_silently:
                raise
            logger.exception("Błąd uwierzytelniania Gmail API: %s", exc)
            return 0

        for message in email_messages:
            try:
                raw_bytes = message.message().as_bytes()
                raw_b64 = base64.urlsafe_b64encode(raw_bytes).decode("ascii")

                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }
                res = requests.post(
                    self.SEND_URL,
                    headers=headers,
                    json={"raw": raw_b64},
                    timeout=self.timeout,
                )

                if res.status_code == 401:
                    # Token mógł wygasnąć - unieważnij i spróbuj odświeżyć raz jeszcze
                    self._access_token = None
                    token = self._get_access_token()
                    headers["Authorization"] = f"Bearer {token}"
                    res = requests.post(
                        self.SEND_URL,
                        headers=headers,
                        json={"raw": raw_b64},
                        timeout=self.timeout,
                    )

                if not res.ok:
                    raise RuntimeError(
                        f"Błąd wysyłki wiadomości Gmail API ({res.status_code}): {res.text}"
                    )

                sent_count += 1
            except Exception as exc:
                if not self.fail_silently:
                    raise
                logger.exception("Błąd wysyłki wiadomości Gmail API: %s", exc)

        return sent_count
