from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

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

        response.data = {
            'error': {
                'code': str(code).upper(),
                'message': message,
                'details': details,
            }
        }
        return response

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
