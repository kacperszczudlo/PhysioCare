"""Uwierzytelnianie użytkowników oparte o tokeny JWT z obsługą ciasteczek HTTP-only."""

from __future__ import annotations

import re
import urllib.parse

from django.conf import settings
from django.http import HttpRequest
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication


def is_trusted_csrf_origin(origin: str) -> bool:
    """Sprawdza, czy podane pochodzenie (Origin) znajduje się na liście zaufanych domen.

    Args:
        origin (str): Adres pochodzenia żądania HTTP (np. https://physiocare-3yh.pages.dev).

    Returns:
        bool: True jeśli pochodzenie jest zaufane lub puste, False w przeciwnym razie.
    """
    if not origin:
        return True

    normalized_origin = origin.rstrip('/')

    # 1. Dokładne dopasowanie do CORS_ALLOWED_ORIGINS lub CSRF_TRUSTED_ORIGINS
    allowed_exact = set(getattr(settings, 'CORS_ALLOWED_ORIGINS', [])) | set(
        getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])
    )
    if any(normalized_origin == allowed.rstrip('/') for allowed in allowed_exact):
        return True

    # 2. Dopasowanie do dozwolonych wyrażeń regularnych CORS
    regexes = getattr(settings, 'CORS_ALLOWED_ORIGIN_REGEXES', [])
    return any(re.match(pattern, normalized_origin) for pattern in regexes)


class CookieJWTAuthentication(JWTAuthentication):
    """Klasa uwierzytelniająca JWT z obsługą tokenów w ciasteczkach HTTP-only i ochroną CSRF.

    Najpierw sprawdza standardowy nagłówek Authorization, a w przypadku jego braku
    odczytuje token dostępowy z ciasteczka HTTP. Dla zapytań modyfikujących stan (POST/PUT/PATCH/DELETE)
    uwierzytelnianych ciasteczkiem egzekwuje weryfikację nagłówka Origin/Referer.
    """

    def authenticate(self, request: HttpRequest | Request | None) -> tuple[object, object] | None:
        """Uwierzytelnia żądanie HTTP na podstawie nagłówka lub ciasteczka.

        Args:
            request (HttpRequest | Request | None): Obiekt żądania HTTP.

        Returns:
            tuple[object, object] | None: Krotka (użytkownik, token) lub None jeśli brak tokenu.

        Raises:
            TypeError: Gdy podany argument request ma niepoprawny typ.
            PermissionDenied: Gdy żądanie modyfikujące stan używa ciasteczka z niezaufanego źródła (CSRF).
        """
        if request is not None and not isinstance(request, (HttpRequest, Request)):
            raise TypeError("Argument 'request' musi być instancją HttpRequest lub Request.")

        if request is None:
            return None

        # 1. Standardowy nagłówek Authorization ma pierwszeństwo
        header = self.get_header(request)
        if header is not None:
            return super().authenticate(request)

        # 2. Odczyt z ciasteczka HTTP
        cookie_name = settings.SIMPLE_JWT.get('AUTH_COOKIE_ACCESS', 'access_token')
        cookies = request.COOKIES if hasattr(request, 'COOKIES') else {}
        raw_token = cookies.get(cookie_name)
        if raw_token is None:
            return None

        # 3. Ochrona CSRF: weryfikacja Origin dla operacji modyfikujących stan przy sesji ciasteczkowej
        self._enforce_cookie_csrf_origin(request)

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token

    def _enforce_cookie_csrf_origin(self, request: HttpRequest | Request) -> None:
        """Blokuje żądania modyfikujące stan wysyłane z niezaufanych witryn (CSRF).

        Args:
            request (HttpRequest | Request): Obiekt żądania HTTP do weryfikacji.

        Raises:
            PermissionDenied: Gdy nagłówek Origin lub Referer wskazuje na niezaufaną domenę.
        """
        method = getattr(request, 'method', 'GET')
        if method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            return

        origin = request.META.get('HTTP_ORIGIN')
        if not origin:
            referer = request.META.get('HTTP_REFERER')
            if referer:
                parsed = urllib.parse.urlparse(referer)
                if parsed.scheme and parsed.netloc:
                    origin = f'{parsed.scheme}://{parsed.netloc}'

        if origin and not is_trusted_csrf_origin(origin):
            raise PermissionDenied('Żądanie międzywitrynowe (CSRF) zablokowane dla nieautoryzowanego pochodzenia.')
