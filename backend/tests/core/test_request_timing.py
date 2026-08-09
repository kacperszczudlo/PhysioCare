"""Tests for request timing / logging middleware."""

from django.http import HttpResponse
from django.test import RequestFactory

from core.middleware import RequestTimingMiddleware


def test_request_timing_headers_and_request_id():
    factory = RequestFactory()
    request = factory.get('/api/v1/health/')

    def get_response(_request):
        return HttpResponse('ok', status=200)

    middleware = RequestTimingMiddleware(get_response)
    response = middleware(request)

    assert 'X-Request-ID' in response
    assert 'X-Response-Time-Ms' in response
    assert request.request_id == response['X-Request-ID']
    assert float(response['X-Response-Time-Ms']) >= 0


def test_request_timing_reuses_incoming_request_id():
    factory = RequestFactory()
    request = factory.get('/api/v1/health/', HTTP_X_REQUEST_ID='client-trace-1')

    def get_response(_request):
        return HttpResponse('ok')

    response = RequestTimingMiddleware(get_response)(request)

    assert response['X-Request-ID'] == 'client-trace-1'
    assert request.request_id == 'client-trace-1'


def test_api_response_includes_timing_headers(api_client):
    response = api_client.get('/api/v1/patients/')
    assert 'X-Request-ID' in response
    assert 'X-Response-Time-Ms' in response
