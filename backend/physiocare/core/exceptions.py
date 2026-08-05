import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger('physiocare.api')


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    request = context.get('request')
    view = context.get('view')
    request_id = getattr(request, 'request_id', None) if request is not None else None
    view_name = view.__class__.__name__ if view is not None else None

    if response is not None:
        code = getattr(exc, 'default_code', 'ERROR')
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                message = 'Walidacja nie powiodła się.'
                details = exc.detail
            elif isinstance(exc.detail, list):
                message = str(exc.detail[0]) if exc.detail else 'Błąd żądania.'
                details = {'messages': [str(item) for item in exc.detail]}
            else:
                message = str(exc.detail)
                details = {}
        else:
            message = 'Wystąpił błąd.'
            details = {}

        error_code = str(code).upper()
        response.data = {
            'error': {
                'code': error_code,
                'message': message,
                'details': details,
            }
        }

        level = logging.ERROR if response.status_code >= 500 else logging.WARNING
        logger.log(
            level,
            'API error: %s',
            message,
            extra={
                'request_id': request_id,
                'method': getattr(request, 'method', None),
                'path': getattr(request, 'path', None),
                'status_code': response.status_code,
                'error_code': error_code,
                'view': view_name,
            },
        )
        return response

    logger.exception(
        'Unhandled server error',
        extra={
            'request_id': request_id,
            'method': getattr(request, 'method', None),
            'path': getattr(request, 'path', None),
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'error_code': 'SERVER_ERROR',
            'view': view_name,
        },
    )

    if not settings.DEBUG:
        return Response(
            {
                'error': {
                    'code': 'SERVER_ERROR',
                    'message': 'Wystąpił nieoczekiwany błąd serwera.',
                    'details': {},
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
