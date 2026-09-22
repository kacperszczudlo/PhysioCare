import logging
import re

from django.conf import settings
from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger: logging.Logger = logging.getLogger('physiocare.api')

_UNIQUE_CONSTRAINT_MESSAGES: dict[str, tuple[str, str]] = {
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

_MAX_LENGTH_EN: re.Pattern[str] = re.compile(
    r'^Ensure this field has no more than (?P<n>\d+) characters\.?$',
    re.IGNORECASE,
)
_MAX_LENGTH_PL_GENERIC: re.Pattern[str] = re.compile(
    r'^Upewnij się, że to pole ma nie więcej niż (?P<n>\d+) znaków\.?$',
    re.IGNORECASE,
)

_ENGLISH_VALIDATION_MESSAGES: dict[str, str] = {
    'Enter a valid email address.': (
        'Podaj prawidłowy adres e-mail (np. jan.kowalski@example.com).'
    ),
    'This field may not be blank.': 'To pole nie może być puste.',
    'This field is required.': 'To pole jest wymagane.',
    'Must be a valid UUID.': 'Podaj prawidłowy kod (UUID).',
}


def _localize_user_message(message: str) -> str:
    """Tłumaczy angielskie lub generyczne komunikaty walidacji DRF na język polski.

    Args:
        message (str): Oryginalna treść komunikatu walidacji.

    Returns:
        str: Przetłumaczony lub przetworzony polski komunikat błędu.

    Raises:
        TypeError: Gdy argument message nie jest napisem.
    """
    if not isinstance(message, str):
        raise TypeError("Argument 'message' musi być typu str.")

    text: str = message.strip()

    if text in _ENGLISH_VALIDATION_MESSAGES:
        return _ENGLISH_VALIDATION_MESSAGES[text]

    match = _MAX_LENGTH_EN.match(text) or _MAX_LENGTH_PL_GENERIC.match(text)
    if match:
        return f'To pole może mieć co najwyżej {match.group("n")} znaków.'

    return text


def _stringify_detail(value: object) -> str | None:
    """Konwertuje zagnieżdżoną strukturę szczegółów błędu na pojedynczy ciąg tekstowy.

    Args:
        value (object): Wartość błędu (str, list, dict lub None).

    Returns:
        str | None: Pierwsza znaleziona przetłumaczona treść błędu lub None.
    """
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
    """Tworzy odpowiedź HTTP 400 Bad Request w przypadku naruszenia więzów unikalności w bazie danych.

    Args:
        exc (IntegrityError): Wyjątek spójności bazy danych.

    Returns:
        Response | None: Obiekt odpowiedzi DRF z kodem CONFLICT lub None.

    Raises:
        TypeError: Gdy exc nie jest instancją IntegrityError.
    """
    if not isinstance(exc, IntegrityError):
        raise TypeError("Argument 'exc' musi być instancją IntegrityError.")

    text: str = str(exc)
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

    match = re.search(r'Key \((?P<field>[^)]+)\)=', text)
    if match or 'unique' in text.lower() or 'unikalności' in text.lower():
        field_name: str = match.group('field') if match else 'detail'
        conflict_message: str = 'Ta wartość jest już zajęta. Sprawdź dane i spróbuj ponownie.'
        return Response(
            {
                'error': {
                    'code': 'CONFLICT',
                    'message': conflict_message,
                    'details': {field_name: [conflict_message]},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return None


def _localize_details(value: object) -> object:
    """Rekurencyjnie lokalizuje komunikaty błędów w strukturze słownika lub listy.

    Args:
        value (object): Struktura błędów (list, dict, str itp.).

    Returns:
        object: Zlokalizowana struktura danych.
    """
    if isinstance(value, list):
        return [_localize_details(item) for item in value]
    if isinstance(value, dict):
        return {key: _localize_details(item) for key, item in value.items()}
    if value is None:
        return value
    return _localize_user_message(str(value))


def custom_exception_handler(exc: Exception, context: dict[str, object]) -> Response | None:
    """Niestandardowy program obsługi wyjątków dla Django REST Framework.

    Args:
        exc (Exception): Zgłoszony wyjątek.
        context (dict[str, object]): Kontekst wykonania widoku (zawierający m.in. request i view).

    Returns:
        Response | None: Sformatowana odpowiedź API lub None.

    Raises:
        TypeError: Gdy exc nie jest instancją Exception lub context nie jest słownikiem.
    """
    if not isinstance(exc, Exception):
        raise TypeError("Argument 'exc' musi być instancją Exception.")
    if not isinstance(context, dict):
        raise TypeError("Argument 'context' musi być słownikiem dict[str, object].")

    request: object = context.get('request')
    view: object = context.get('view')
    request_id: str | None = request.request_id if request is not None and hasattr(request, 'request_id') else None
    view_name: str | None = view.__class__.__name__ if view is not None else None

    if isinstance(exc, IntegrityError):
        conflict: Response | None = _integrity_conflict_response(exc)
        if conflict is not None:
            logger.warning(
                'API error: %s',
                conflict.data['error']['message'],
                extra={
                    'request_id': request_id,
                    'method': request.method if request is not None and hasattr(request, 'method') else None,
                    'path': request.path if request is not None and hasattr(request, 'path') else None,
                    'status_code': conflict.status_code,
                    'error_code': 'CONFLICT',
                    'view': view_name,
                },
            )
            return conflict

    response: Response | None = exception_handler(exc, context)

    if response is not None:
        code: object = exc.default_code if hasattr(exc, 'default_code') else 'ERROR'
        message: str = 'Wystąpił błąd.'
        details: object = {}

        if hasattr(exc, 'detail'):
            detail_obj: object = exc.detail
            if isinstance(detail_obj, dict):
                details = _localize_details(detail_obj)
                message = _stringify_detail(details) or 'Walidacja nie powiodła się.'
            elif isinstance(detail_obj, list):
                localized: list[str] = [_localize_user_message(str(item)) for item in detail_obj]
                message = localized[0] if localized else 'Błąd żądania.'
                details = {'messages': localized}
            else:
                message = _localize_user_message(str(detail_obj))
                details = {}
        else:
            message = 'Wystąpił błąd.'
            details = {}

        error_code: str = str(code).upper()
        response.data = {
            'error': {
                'code': error_code,
                'message': message,
                'details': details,
            }
        }

        level: int = logging.ERROR if response.status_code >= 500 else logging.WARNING
        logger.log(
            level,
            'API error: %s',
            message,
            extra={
                'request_id': request_id,
                'method': request.method if request is not None and hasattr(request, 'method') else None,
                'path': request.path if request is not None and hasattr(request, 'path') else None,
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
            'method': request.method if request is not None and hasattr(request, 'method') else None,
            'path': request.path if request is not None and hasattr(request, 'path') else None,
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'error_code': 'SERVER_ERROR',
            'view': view_name,
        },
    )

    server_error_message: str = (
        'Wystąpił nieoczekiwany błąd serwera.'
        if not settings.DEBUG
        else 'Wystąpił nieoczekiwany błąd serwera. Szczegóły są w logach backendu.'
    )
    return Response(
        {
            'error': {
                'code': 'SERVER_ERROR',
                'message': server_error_message,
                'details': {},
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
