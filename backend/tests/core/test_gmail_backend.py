from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMessage

from core.gmail_backend import EmailBackend, GmailApiEmailBackend, GmailEmailBackend


class TestGmailEmailBackend:
    """Testy jednostkowe backendu wysyłki e-maili przez Gmail REST API."""

    def test_class_aliases(self) -> None:
        """Sprawdza czy aliasy EmailBackend i GmailApiEmailBackend wskazują na GmailEmailBackend."""
        assert EmailBackend is GmailEmailBackend
        assert GmailApiEmailBackend is GmailEmailBackend

    def test_missing_credentials_raises_improperly_configured(self) -> None:
        """Sprawdza czy brakujące dane uwierzytelniania rzucają ImproperlyConfigured."""
        backend = GmailEmailBackend(
            client_id='',
            client_secret='',
            refresh_token='',
            fail_silently=False,
        )
        msg = EmailMessage('Test', 'Body', 'from@test.pl', ['to@test.pl'])
        with pytest.raises(ImproperlyConfigured) as exc_info:
            backend.send_messages([msg])
        assert 'Wymagane zmienne GMAIL_CLIENT_ID' in str(exc_info.value)

    def test_missing_credentials_fail_silently(self) -> None:
        """Sprawdza czy przy fail_silently=True brak danych zwraca 0 wysłanych wiadomości."""
        backend = GmailApiEmailBackend(
            client_id='',
            client_secret='',
            refresh_token='',
            fail_silently=True,
        )
        msg = EmailMessage('Test', 'Body', 'from@test.pl', ['to@test.pl'])
        sent = backend.send_messages([msg])
        assert sent == 0

    @patch('core.gmail_backend.requests.post')
    def test_successful_send(self, mock_post: MagicMock) -> None:
        """Sprawdza poprawną wysyłkę e-maila po uzyskaniu tokena."""
        token_response = MagicMock(ok=True, status_code=200)
        token_response.json.return_value = {
            'access_token': 'test-access-token-123',
            'expires_in': 3600,
        }

        send_response = MagicMock(ok=True, status_code=200)
        send_response.json.return_value = {'id': 'msg-123'}

        mock_post.side_effect = [token_response, send_response]

        backend = GmailApiEmailBackend(
            client_id='test-client-id',
            client_secret='test-client-secret',
            refresh_token='test-refresh-token',
        )
        msg = EmailMessage(
            subject='Witamy w PhysioCare',
            body='Treść powitalna',
            from_email='kontakt@physiocare.pl',
            to=['pacjent@example.com'],
        )

        sent = backend.send_messages([msg])
        assert sent == 1
        assert mock_post.call_count == 2

        # Pierwsze zapytanie: odświeżenie tokena OAuth
        token_call_args, token_call_kwargs = mock_post.call_args_list[0]
        assert token_call_args[0] == 'https://oauth2.googleapis.com/token'
        assert token_call_kwargs['data']['grant_type'] == 'refresh_token'
        assert token_call_kwargs['data']['refresh_token'] == 'test-refresh-token'

        # Drugie zapytanie: wysyłka do Gmail API
        send_call_args, send_call_kwargs = mock_post.call_args_list[1]
        assert send_call_args[0] == 'https://gmail.googleapis.com/gmail/v1/users/me/messages/send'
        assert send_call_kwargs['headers']['Authorization'] == 'Bearer test-access-token-123'
        assert 'raw' in send_call_kwargs['json']

    @patch('core.gmail_backend.requests.post')
    def test_token_refresh_retry_on_401(self, mock_post: MagicMock) -> None:
        """Sprawdza ponowienie wysyłki po odświeżeniu tokena gdy API zwróci 401."""
        token_response_1 = MagicMock(ok=True, status_code=200)
        token_response_1.json.return_value = {'access_token': 'expired-token', 'expires_in': 3600}

        send_response_401 = MagicMock(ok=False, status_code=401, text='Token expired')

        token_response_2 = MagicMock(ok=True, status_code=200)
        token_response_2.json.return_value = {'access_token': 'fresh-token', 'expires_in': 3600}

        send_response_ok = MagicMock(ok=True, status_code=200)
        send_response_ok.json.return_value = {'id': 'msg-456'}

        mock_post.side_effect = [
            token_response_1,
            send_response_401,
            token_response_2,
            send_response_ok,
        ]

        backend = GmailApiEmailBackend(
            client_id='test-client-id',
            client_secret='test-client-secret',
            refresh_token='test-refresh-token',
        )
        msg = EmailMessage('Temat', 'Treść', 'nadawca@test.pl', ['odbiorca@test.pl'])

        sent = backend.send_messages([msg])
        assert sent == 1
        assert mock_post.call_count == 4
