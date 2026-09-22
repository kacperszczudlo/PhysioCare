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

