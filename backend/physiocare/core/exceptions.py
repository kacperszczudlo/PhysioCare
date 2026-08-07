import logging
import re

from django.conf import settings
from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger('physiocare.api')

# Map known unique constraints to field + Polish user-facing message.
_UNIQUE_CONSTRAINT_MESSAGES = {
    'therapist_profiles_pwzf_number_key': (
        'pwzf_number',
        'Konto z tym numerem PWZFz już istnieje. Zaloguj się lub użyj innego numeru.',
    ),
    'users_email_key': (
        'email',
        'Ten adres e-mail jest już zarejestrowany. Zaloguj się lub użyj innego adresu.',
    ),
    'accounts_customuser_email_key': (
        'email',
        'Ten adres e-mail jest już zarejestrowany. Zaloguj się lub użyj innego adresu.',
    ),
    'exclude_overlapping_exercise_assignments': (
        'exercise_id',
        'To ćwiczenie jest już przypisane temu pacjentowi w nakładającym się okresie.',
    ),
}


_MAX_LENGTH_EN = re.compile(
    r'^Ensure this field has no more than (?P<n>\d+) characters\.?$',
    re.IGNORECASE,
)
_MAX_LENGTH_PL_GENERIC = re.compile(
    r'^Upewnij się, że to pole ma nie więcej niż (?P<n>\d+) znaków\.?$',
    re.IGNORECASE,
)

_ENGLISH_VALIDATION_MESSAGES = {
    'Enter a valid email address.': (
        'Podaj prawidłowy adres e-mail (np. jan.kowalski@example.com).'
    ),
    'This field may not be blank.': 'To pole nie może być puste.',
    'This field is required.': 'To pole jest wymagane.',
    'Must be a valid UUID.': 'Podaj prawidłowy kod (UUID).',
}


def _localize_user_message(message: str) -> str:
    """Translate leftover English/generic DRF validation text to Polish."""
    text = str(message).strip()
    if text in _ENGLISH_VALIDATION_MESSAGES:
        return _ENGLISH_VALIDATION_MESSAGES[text]

    match = _MAX_LENGTH_EN.match(text) or _MAX_LENGTH_PL_GENERIC.match(text)
    if match:
        return f'To pole może mieć co najwyżej {match.group("n")} znaków.'

    return text


def _stringify_detail(value):
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        if not value:
            return None
        return _stringify_detail(value[0])
    if isinstance(value, dict):
        for nested in value.values():
            message = _stringify_detail(nested)
            if message:
                return message
        return None
    return _localize_user_message(str(value))


def _integrity_conflict_response(exc: IntegrityError) -> Response | None:
    text = str(exc)
    for constraint, (field, message) in _UNIQUE_CONSTRAINT_MESSAGES.items():
        if constraint in text:
            return Response(
                {
                    'error': {
                        'code': 'CONFLICT',
                        'message': message,
                        'details': {field: [message]},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    # Generic unique violation: "Key (column)=(value) already exists."
    match = re.search(r'Key \((?P<field>[^)]+)\)=', text)
    if match or 'unique' in text.lower() or 'unikalności' in text.lower():
        field = match.group('field') if match else 'detail'
        message = 'Ta wartość jest już zajęta. Sprawdź dane i spróbuj ponownie.'
        return Response(
            {
                'error': {
                    'code': 'CONFLICT',
                    'message': message,
                    'details': {field: [message]},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return None


def _localize_details(value):
    if isinstance(value, list):
        return [_localize_details(item) for item in value]
    if isinstance(value, dict):
        return {key: _localize_details(item) for key, item in value.items()}
    if value is None:
        return value
    return _localize_user_message(str(value))


def custom_exception_handler(exc, context):
    request = context.get('request')
    view = context.get('view')
    request_id = getattr(request, 'request_id', None) if request is not None else None
    view_name = view.__class__.__name__ if view is not None else None

    if isinstance(exc, IntegrityError):
        conflict = _integrity_conflict_response(exc)
        if conflict is not None:
            logger.warning(
                'API error: %s',
                conflict.data['error']['message'],
                extra={
                    'request_id': request_id,
                    'method': getattr(request, 'method', None),
                    'path': getattr(request, 'path', None),
                    'status_code': conflict.status_code,
                    'error_code': 'CONFLICT',
                    'view': view_name,
                },
            )
            return conflict

    response = exception_handler(exc, context)

    if response is not None:
        code = getattr(exc, 'default_code', 'ERROR')
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                details = _localize_details(exc.detail)
                message = _stringify_detail(details) or 'Walidacja nie powiodła się.'
            elif isinstance(exc.detail, list):
                localized = [_localize_user_message(str(item)) for item in exc.detail]
                message = localized[0] if localized else 'Błąd żądania.'
                details = {'messages': localized}
            else:
                message = _localize_user_message(str(exc.detail))
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

    # Always return JSON so the SPA never falls back to a blank "Błąd serwera".
    message = (
        'Wystąpił nieoczekiwany błąd serwera.'
        if not settings.DEBUG
        else 'Wystąpił nieoczekiwany błąd serwera. Szczegóły są w logach backendu.'
    )
    return Response(
        {
            'error': {
                'code': 'SERVER_ERROR',
                'message': message,
                'details': {},
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
