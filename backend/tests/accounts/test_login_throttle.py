import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_login_throttle_blocks_repeated_failures(api_client):
    cache.clear()
    url = reverse('login')

    for _ in range(5):
        response = api_client.post(
            url,
            {'email': 'unknown@example.com', 'password': 'wrong'},
            format='json',
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = api_client.post(
        url,
        {'email': 'unknown@example.com', 'password': 'wrong'},
        format='json',
    )
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
