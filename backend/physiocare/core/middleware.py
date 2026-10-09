from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound

logger = logging.getLogger('physiocare.api')

_SKIP_PREFIXES: tuple[str, ...] = ('/static/', '/media/', '/favicon.ico')


def get_client_ip(request: HttpRequest) -> str:
    """Pobiera rzeczywisty adres IP klienta z uwzględnieniem Cloudflare oraz nagłówków proxy.

    Args:
        request (HttpRequest): Obiekt żądania HTTP.

    Returns:
        str: Adres IP klienta lub pusty ciąg.
    """
    if not hasattr(request, 'META'):
        return ''
    cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_ip:
        return cf_ip.strip()
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '').strip()


class AdminAccessMiddleware:
    """Ogranicza dostęp do panelu administracyjnego Django na podstawie flagi konfiguracyjnej oraz białej listy IP."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Inicjalizuje oprogramowanie pośredniczące.

        Args:
            get_response (Callable[[HttpRequest], HttpResponse]): Funkcja pobierająca odpowiedź HTTP.

        Raises:
            TypeError: Gdy get_response jest None.
        """
        if get_response is None:
            raise TypeError("Argument 'get_response' nie może być None.")
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Obsługuje żądanie wejściowe i sprawdza uprawnienia dostępu do ścieżki /admin.

        Args:
            request (HttpRequest): Obiekt żądania HTTP.

        Returns:
            HttpResponse: Odpowiedź HTTP.

        Raises:
            TypeError: Gdy request nie jest instancją HttpRequest.
        """
        if not isinstance(request, HttpRequest):
            raise TypeError("Argument 'request' musi być instancją HttpRequest.")

        path = request.path
        if (
            path == '/admin'
            or path.startswith('/admin/')
            or path == '/api/v1/admin'
            or path.startswith('/api/v1/admin/')
        ):
            admin_enabled = settings.ADMIN_ENABLED if hasattr(settings, 'ADMIN_ENABLED') else True
            if not admin_enabled:
                return HttpResponseNotFound()

            allowed_ips = (settings.ADMIN_ALLOWED_IPS if hasattr(settings, 'ADMIN_ALLOWED_IPS') else None) or []
            if allowed_ips:
                client_ip = get_client_ip(request)
                if client_ip not in allowed_ips:
                    return HttpResponseNotFound()

        return self.get_response(request)


class RequestTimingMiddleware:
    """Przypisuje identyfikator żądania (X-Request-ID), mierzy czas wykonania oraz generuje ustrukturyzowane logi API."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Inicjalizuje oprogramowanie pośredniczące.

        Args:
            get_response (Callable[[HttpRequest], HttpResponse]): Funkcja pobierająca odpowiedź HTTP.

        Raises:
            TypeError: Gdy get_response jest None.
        """
        if get_response is None:
            raise TypeError("Argument 'get_response' nie może być None.")
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Mierzy czas przetworzenia żądania i dodaje nagłówki diagnostyczne do odpowiedzi.

        Args:
            request (HttpRequest): Obiekt żądania HTTP.

        Returns:
            HttpResponse: Zmodyfikowany obiekt odpowiedzi HTTP.

        Raises:
            TypeError: Gdy request nie jest instancją HttpRequest.
        """
        if not isinstance(request, HttpRequest):
            raise TypeError("Argument 'request' musi być instancją HttpRequest.")

        request_id = request.headers.get('X-Request-ID') if hasattr(request, 'headers') else None
        if not request_id:
            request_id = str(uuid.uuid4())

        request.request_id = request_id
        started = time.perf_counter()

        response = self.get_response(request)

        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        response['X-Request-ID'] = request_id
        response['X-Response-Time-Ms'] = f'{duration_ms:.1f}'

        path = request.path if hasattr(request, 'path') else ''
        if any(path.startswith(prefix) for prefix in _SKIP_PREFIXES):
            return response

        status_code = response.status_code
        level = logging.INFO
        if status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING

        user = request.user if hasattr(request, 'user') else None
        user_id = (
            str(user.pk)
            if user is not None and hasattr(user, 'is_authenticated') and user.is_authenticated
            else None
        )

        logger.log(
            level,
            'request completed',
            extra={
                'request_id': request_id,
                'method': request.method if hasattr(request, 'method') else None,
                'path': path,
                'status_code': status_code,
                'duration_ms': duration_ms,
                'user_id': user_id,
            },
        )
        return response


class SecurityHeadersMiddleware:
    """Dołącza polityki bezpieczeństwa CSP, Permissions-Policy oraz COOP do odpowiedzi HTTP."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Inicjalizuje oprogramowanie pośredniczące.

        Args:
            get_response (Callable[[HttpRequest], HttpResponse]): Funkcja pobierająca odpowiedź HTTP.

        Raises:
            TypeError: Gdy get_response jest None.
        """
        if get_response is None:
            raise TypeError("Argument 'get_response' nie może być None.")
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Ustawia nagłówki bezpieczeństwa w odpowiedzi HTTP.

        Args:
            request (HttpRequest): Obiekt żądania HTTP.

        Returns:
            HttpResponse: Zmodyfikowana odpowiedź HTTP z nagłówkami bezpieczeństwa.

        Raises:
            TypeError: Gdy request nie jest instancją HttpRequest.
        """
        if not isinstance(request, HttpRequest):
            raise TypeError("Argument 'request' musi być instancją HttpRequest.")

        response = self.get_response(request)

        if 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' "
                "https://www.google.com/recaptcha/ https://www.gstatic.com/recaptcha/ "
                "https://accounts.google.com/gsi/ https://apis.google.com; "
                "style-src 'self' 'unsafe-inline' https://accounts.google.com/gsi/style https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com data:; "
                "img-src 'self' data: blob: https://*.googleusercontent.com https://www.gstatic.com; "
                "connect-src 'self' https: wss: http://localhost:* ws://localhost:* https://www.google.com "
                "https://accounts.google.com https://exp.host https://*.sentry.io; "
                "frame-src 'self' https://www.google.com/recaptcha/ https://recaptcha.google.com/ "
                "https://accounts.google.com/; "
                "frame-ancestors 'none'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )

        if 'Permissions-Policy' not in response:
            response['Permissions-Policy'] = (
                "camera=(), microphone=(), geolocation=(), payment=(), usb=(), display-capture=()"
            )

        if 'Cross-Origin-Opener-Policy' not in response:
            response['Cross-Origin-Opener-Policy'] = "same-origin-allow-popups"

        return response


