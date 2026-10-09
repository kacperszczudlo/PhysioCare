from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory

from core.middleware import RequestTimingMiddleware


def test_request_timing_headers_and_request_id() -> None:
    """Sprawdza generowanie nagłówków X-Request-ID oraz X-Response-Time-Ms przez middleware czasu żądania."""
    # Arrange
    factory: RequestFactory = RequestFactory()
    request: HttpRequest = factory.get('/api/v1/health/')

    def get_response(_req: HttpRequest) -> HttpResponse:
        return HttpResponse('ok', status=200)

    middleware: RequestTimingMiddleware = RequestTimingMiddleware(get_response)
    response: HttpResponse = middleware(request)

    # Assert
    assert 'X-Request-ID' in response
    assert 'X-Response-Time-Ms' in response
    assert request.request_id == response['X-Request-ID']
    assert float(response['X-Response-Time-Ms']) >= 0


def test_request_timing_reuses_incoming_request_id() -> None:
    """Sprawdza ponowne użycie przychodzącego nagłówka X-Request-ID ze strumienia klienta."""
    # Arrange
    factory: RequestFactory = RequestFactory()
    request: HttpRequest = factory.get('/api/v1/health/', HTTP_X_REQUEST_ID='client-trace-1')

    def get_response(_req: HttpRequest) -> HttpResponse:
        return HttpResponse('ok')

    response: HttpResponse = RequestTimingMiddleware(get_response)(request)

    # Assert
    assert response['X-Request-ID'] == 'client-trace-1'
    assert request.request_id == 'client-trace-1'


def test_api_response_includes_timing_headers(api_client: object) -> None:
    """Sprawdza, czy odpowiedzi z punktów końcowych API zawierają nagłówki czasowe."""
    # Arrange
    response: object = api_client.get('/api/v1/patients/')
    # Assert
    assert 'X-Request-ID' in response
    assert 'X-Response-Time-Ms' in response


def test_structured_json_formatter_handles_uuid_and_extra_fields() -> None:
    """Sprawdza, czy StructuredJsonFormatter poprawnie serializuje identyfikatory UUID bez błędu TypeError."""
    import json
    import logging
    import uuid

    from core.logging_formatters import StructuredJsonFormatter

    formatter = StructuredJsonFormatter()
    record = logging.LogRecord(
        name='physiocare.api',
        level=logging.INFO,
        pathname='middleware.py',
        lineno=125,
        msg='request completed',
        args=(),
        exc_info=None,
    )
    user_uuid = uuid.uuid4()
    req_uuid = uuid.uuid4()
    record.request_id = req_uuid
    record.user_id = user_uuid
    record.method = 'GET'
    record.path = '/api/v1/me/profile/'
    record.status_code = 200
    record.duration_ms = 12.5

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed['message'] == 'request completed'
    assert parsed['user_id'] == str(user_uuid)
    assert parsed['request_id'] == str(req_uuid)
    assert parsed['status_code'] == 200


def test_get_client_ip_prioritizes_cf_and_forwarded_headers() -> None:
    """Sprawdza ekstrakcję rzeczywistego adresu IP z nagłówków Cloudflare i proxy."""
    from core.middleware import get_client_ip
    factory = RequestFactory()

    # Cloudflare CF-Connecting-IP
    req_cf = factory.get('/', HTTP_CF_CONNECTING_IP='203.0.113.195', REMOTE_ADDR='10.0.0.1')
    assert get_client_ip(req_cf) == '203.0.113.195'

    # X-Forwarded-For (pierwszy adres w łańcuchu)
    req_xff = factory.get('/', HTTP_X_FORWARDED_FOR='198.51.100.42, 10.0.0.2', REMOTE_ADDR='10.0.0.1')
    assert get_client_ip(req_xff) == '198.51.100.42'

    # Bez nagłówków proxy -> fallback do REMOTE_ADDR
    req_remote = factory.get('/', REMOTE_ADDR='192.0.2.1')
    assert get_client_ip(req_remote) == '192.0.2.1'


