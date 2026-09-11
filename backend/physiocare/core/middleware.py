"""HTTP request logging, admin hardening, and response-time metrics."""

from __future__ import annotations

import logging
import time
import uuid

from django.conf import settings
from django.http import HttpResponseNotFound

logger = logging.getLogger('physiocare.api')

_SKIP_PREFIXES = ('/static/', '/media/', '/favicon.ico')


class AdminAccessMiddleware:
    """Restrict Django admin by enable flag and optional IP allowlist."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path == '/admin' or path.startswith('/admin/'):
            if not getattr(settings, 'ADMIN_ENABLED', True):
                return HttpResponseNotFound()

            allowed_ips = getattr(settings, 'ADMIN_ALLOWED_IPS', None) or []
            if allowed_ips:
                client_ip = request.META.get('REMOTE_ADDR', '')
                if client_ip not in allowed_ips:
                    return HttpResponseNotFound()

        return self.get_response(request)


class RequestTimingMiddleware:
    """Attach request id, measure duration, and emit structured API logs."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        request.request_id = request_id
        started = time.perf_counter()

        response = self.get_response(request)

        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        response['X-Request-ID'] = request_id
        response['X-Response-Time-Ms'] = f'{duration_ms:.1f}'

        path = request.path
        if any(path.startswith(prefix) for prefix in _SKIP_PREFIXES):
            return response

        status_code = response.status_code
        level = logging.INFO
        if status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING

        user = getattr(request, 'user', None)
        user_id = getattr(user, 'pk', None) if user is not None and getattr(user, 'is_authenticated', False) else None

        logger.log(
            level,
            'request completed',
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': path,
                'status_code': status_code,
                'duration_ms': duration_ms,
                'user_id': user_id,
            },
        )
        return response


class SecurityHeadersMiddleware:
    """Attach CSP, Permissions-Policy, and COOP security headers to HTTP responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
                "https://www.google.com/recaptcha/ https://www.gstatic.com/recaptcha/ "
                "https://accounts.google.com/gsi/ https://apis.google.com; "
                "style-src 'self' 'unsafe-inline' https://accounts.google.com/gsi/style https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com data:; "
                "img-src 'self' data: blob: https://*.googleusercontent.com https://www.gstatic.com; "
                "connect-src 'self' http://localhost:* ws://localhost:* https://www.google.com "
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

