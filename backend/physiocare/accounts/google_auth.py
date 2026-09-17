from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token


class GoogleAuthError(Exception):
    """Wyjątek zgłaszany w przypadku braku akceptacji tokenu Google ID Token."""

    def __init__(self, code: str, message: str, *, http_status: int = 401) -> None:
        """Inicjalizuje błąd autoryzacji Google.

        Args:
            code (str): Kod błędu.
            message (str): Komunikat błędu.
            http_status (int): Status odpowiedzi HTTP.
        """
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status


@dataclass(frozen=True, slots=True)
class GoogleIdentity:
    """Reprezentacja zwalidowanych danych tożsamości z konta Google."""

    sub: str
    email: str
    email_verified: bool
    given_name: str
    family_name: str


def configured_google_client_ids() -> list[str]:
    """Zwraca listę skonfigurowanych identyfikatorów klienta Google (GOOGLE_CLIENT_IDS).

    Returns:
        list[str]: Lista identyfikatorów aplikacji.
    """
    client_ids = settings.GOOGLE_CLIENT_IDS if hasattr(settings, 'GOOGLE_CLIENT_IDS') else []
    return list(client_ids or [])


def extract_google_credential(data) -> str | None:
    """Odczytuje token logowania GIS / Google Sign-In z powszechnych nazw pól żądania.

    Args:
        data: Słownik lub obiekt danych żądania.

    Returns:
        str | None: Ciąg tokenu lub None.
    """
    if not hasattr(data, 'get'):
        return None
    raw = data.get('credential') or data.get('id_token') or data.get('google_credential')
    if raw is None:
        return None
    value = str(raw).strip()
    return value or None


def verify_google_id_token(credential: str) -> GoogleIdentity:
    """Weryfikuje token ID Google Sign-In i zwraca znormalizowaną tożsamość.

    Args:
        credential (str): Ciąg tokenu ID Google.

    Returns:
        GoogleIdentity: Znormalizowany obiekt danych tożsamości.

    Raises:
        GoogleAuthError: Gdy token nie może zostać zweryfikowany.
    """
    client_ids = configured_google_client_ids()
    if not client_ids:
        raise GoogleAuthError(
            'AUTH_020',
            'Logowanie Google nie jest skonfigurowane po stronie serwera.',
            http_status=503,
        )

    if not credential or not isinstance(credential, str) or not credential.strip():
        raise GoogleAuthError(
            'AUTH_021',
            'Brak tokenu Google.',
            http_status=400,
        )

    try:
        payload = id_token.verify_oauth2_token(
            credential.strip(),
            google_requests.Request(),
            audience=client_ids,
        )
    except ValueError as exc:
        raise GoogleAuthError(
            'AUTH_022',
            'Nie udało się zweryfikować logowania Google.',
            http_status=401,
        ) from exc

    email = (payload.get('email') or '').strip().lower()
    sub = (payload.get('sub') or '').strip()
    if not email or not sub:
        raise GoogleAuthError(
            'AUTH_022',
            'Brak wymaganych danych z konta Google.',
            http_status=401,
        )

    if payload.get('email_verified') is False:
        raise GoogleAuthError(
            'AUTH_022',
            'Adres e-mail w Google musi być zweryfikowany.',
            http_status=401,
        )

    return GoogleIdentity(
        sub=sub,
        email=email,
        email_verified=bool(payload.get('email_verified', True)),
        given_name=(payload.get('given_name') or '').strip(),
        family_name=(payload.get('family_name') or '').strip(),
    )

