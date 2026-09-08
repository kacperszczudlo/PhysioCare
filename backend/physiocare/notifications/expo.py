import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger('physiocare.notifications')

EXPO_PUSH_URL = 'https://exp.host/--/api/v2/push/send'


class ExpoPushError(Exception):
    pass


def send_expo_push(messages: list[dict]) -> list[dict]:
    """Send Expo push tickets. `messages` is a list of Expo message dicts."""
    if not messages:
        return []

    url = getattr(settings, 'EXPO_PUSH_URL', EXPO_PUSH_URL)
    payload = json.dumps(messages).encode('utf-8')
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    timeout = getattr(settings, 'EXPO_PUSH_TIMEOUT', 10)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode('utf-8') or '{}')
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ExpoPushError(str(exc)) from exc

    tickets = body.get('data', [])
    if isinstance(tickets, dict):
        tickets = [tickets]
    if not isinstance(tickets, list):
        raise ExpoPushError('Nieoczekiwana odpowiedź Expo Push.')
    return tickets
