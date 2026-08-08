import pytest
from django.test import override_settings


@pytest.mark.django_db
@override_settings(ADMIN_ENABLED=False)
def test_admin_disabled_returns_404(client):
    response = client.get('/admin/')
    assert response.status_code == 404


@pytest.mark.django_db
@override_settings(ADMIN_ENABLED=True, ADMIN_ALLOWED_IPS=['203.0.113.10'])
def test_admin_ip_allowlist_blocks_other_clients(client):
    response = client.get('/admin/', REMOTE_ADDR='198.51.100.1')
    assert response.status_code == 404


@pytest.mark.django_db
@override_settings(ADMIN_ENABLED=True, ADMIN_ALLOWED_IPS=['203.0.113.10'])
def test_admin_ip_allowlist_allows_listed_client(client):
    response = client.get('/admin/', REMOTE_ADDR='203.0.113.10')
    # Reach admin login (or redirect), not middleware 404.
    assert response.status_code in (200, 302)


@pytest.mark.django_db
@override_settings(ADMIN_ENABLED=True, ADMIN_ALLOWED_IPS=[])
def test_admin_enabled_without_ip_filter(client):
    response = client.get('/admin/')
    assert response.status_code in (200, 302)
