"""HTTP request logging and response-time metrics."""

from __future__ import annotations

import logging
import time
import uuid

logger = logging.getLogger('physiocare.api')

_SKIP_PREFIXES = ('/static/', '/media/', '/favicon.ico')


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
