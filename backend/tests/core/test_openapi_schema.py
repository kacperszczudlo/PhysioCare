import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_openapi_schema_endpoint():
    client = APIClient()
    response = client.get('/api/v1/schema/')
    assert response.status_code == status.HTTP_200_OK
    assert 'openapi' in response.data or 'openapi' in response.content.decode()


@pytest.mark.django_db
def test_swagger_ui_endpoint():
    client = APIClient()
    response = client.get('/api/v1/docs/')
    assert response.status_code == status.HTTP_200_OK
