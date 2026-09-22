import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger: logging.Logger = logging.getLogger('physiocare.notifications')

EXPO_PUSH_URL: str = 'https://exp.host/--/api/v2/push/send'


class ExpoPushError(Exception):
    """Błąd wysyłania lub przetwarzania odpowiedzi z serwera Expo Push."""


def send_expo_push(messages: list[dict[str, object]]) -> list[dict[str, object]]:
    """Wysyła bilety powiadomień push do usługi Expo.

    Args:
        messages (list[dict[str, object]]): Lista słowników reprezentujących komunikaty Expo.

    Returns:
        list[dict[str, object]]: Lista zwrotnych biletów (tickets) od Expo.

    Raises:
        TypeError: Gdy argument messages nie jest listą.
        ExpoPushError: Gdy nastąpi błąd połączenia, przekroczenie czasu lub nieprawidłowa odpowiedź.
    """
    if not isinstance(messages, list):
        raise TypeError("Parametr 'messages' musi być listą słowników list[dict[str, object]].")

    if not messages:
        return []

    url: str = settings.EXPO_PUSH_URL if hasattr(settings, 'EXPO_PUSH_URL') else EXPO_PUSH_URL
    payload: bytes = json.dumps(messages).encode('utf-8')
    request: urllib.request.Request = urllib.request.Request(
        url,
        data=payload,
        headers={
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    timeout_val: object = settings.EXPO_PUSH_TIMEOUT if hasattr(settings, 'EXPO_PUSH_TIMEOUT') else 10
    timeout: int = int(timeout_val) if isinstance(timeout_val, (int, float, str)) else 10

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body: dict[str, object] = json.loads(response.read().decode('utf-8') or '{}')
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ExpoPushError(str(exc)) from exc

    tickets: object = body.get('data', [])
    if isinstance(tickets, dict):
        tickets = [tickets]
    if not isinstance(tickets, list):
        raise ExpoPushError('Nieoczekiwana odpowiedź Expo Push.')

    return tickets
