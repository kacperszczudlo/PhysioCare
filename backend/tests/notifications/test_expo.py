import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from notifications.expo import ExpoPushError, send_expo_push


def test_send_expo_push_empty_messages_returns_empty():
    assert send_expo_push([]) == []


@patch('urllib.request.urlopen')
def test_send_expo_push_success(mock_urlopen):
    # Arrange
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"data": [{"status": "ok", "id": "ticket-123"}]}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    messages = [{'to': 'ExponentPushToken[xxx]', 'title': 'Test', 'body': 'Hello'}]

    # Act
    tickets = send_expo_push(messages)

    # Assert
    assert len(tickets) == 1
    assert tickets[0]['status'] == 'ok'
    assert tickets[0]['id'] == 'ticket-123'


@patch('urllib.request.urlopen', side_effect=urllib.error.URLError('Network down'))
def test_send_expo_push_network_error_raises_expo_push_error(mock_urlopen):
    messages = [{'to': 'ExponentPushToken[xxx]', 'title': 'Test', 'body': 'Hello'}]

    with pytest.raises(ExpoPushError) as exc_info:
        send_expo_push(messages)
    assert 'Network down' in str(exc_info.value)


@patch('urllib.request.urlopen')
def test_send_expo_push_invalid_json_raises_expo_push_error(mock_urlopen):
    mock_response = MagicMock()
    mock_response.read.return_value = b'invalid json'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    messages = [{'to': 'ExponentPushToken[xxx]', 'title': 'Test', 'body': 'Hello'}]

    with pytest.raises(ExpoPushError):
        send_expo_push(messages)


@patch('urllib.request.urlopen')
def test_send_expo_push_unexpected_response_format_raises_expo_push_error(mock_urlopen):
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"data": "not a list or dict"}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    messages = [{'to': 'ExponentPushToken[xxx]', 'title': 'Test', 'body': 'Hello'}]

    with pytest.raises(ExpoPushError) as exc_info:
        send_expo_push(messages)
    assert 'Nieoczekiwana odpowiedź Expo Push.' in str(exc_info.value)
