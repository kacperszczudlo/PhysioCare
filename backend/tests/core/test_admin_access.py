import pytest
from django.test import override_settings


@pytest.mark.django_db
@override_settings(ADMIN_ENABLED=False)
def test_admin_disabled_returns_404(client: object) -> None:
    """Sprawdza, czy przy wyłączonym panelu admina próba wejścia zwraca błąd 404."""
    # Act
    response = client.get('/admin/')
    # Assert
    assert response.status_code == 404


@pytest.mark.django_db
@override_settings(ADMIN_ENABLED=True, ADMIN_ALLOWED_IPS=['203.0.113.10'])
def test_admin_ip_allowlist_blocks_other_clients(client: object) -> None:
    """Sprawdza, czy lista dozwolonych IP dla admina blokuje klientów spoza listy."""
    # Act
    response = client.get('/admin/', REMOTE_ADDR='198.51.100.1')
    # Assert
    assert response.status_code == 404


@pytest.mark.django_db
@override_settings(ADMIN_ENABLED=True, ADMIN_ALLOWED_IPS=['203.0.113.10'])
def test_admin_ip_allowlist_allows_listed_client(client: object) -> None:
    """Sprawdza, czy klient z listy dozwolonych IP ma dostęp do panelu admina."""
    # Act
    response = client.get('/admin/', REMOTE_ADDR='203.0.113.10')
    # Assert
    assert response.status_code in (200, 302)


@pytest.mark.django_db
@override_settings(ADMIN_ENABLED=True, ADMIN_ALLOWED_IPS=[])
def test_admin_enabled_without_ip_filter(client: object) -> None:
    """Sprawdza dostęp do admina gdy opcja jest włączona bez filtrowania IP."""
    # Act
    response = client.get('/admin/')
    # Assert
    assert response.status_code in (200, 302)


@pytest.mark.django_db
@override_settings(ADMIN_ENABLED=False)
def test_api_admin_disabled_returns_404(client: object) -> None:
    """Sprawdza, czy wyłączenie admina blokuje również API pod /api/v1/admin/."""
    response = client.get('/api/v1/admin/dashboard/')
    assert response.status_code == 404


@pytest.mark.django_db
@override_settings(ADMIN_ENABLED=True, ADMIN_ALLOWED_IPS=['203.0.113.10'])
def test_api_admin_ip_allowlist_blocks_other_clients(client: object) -> None:
    """Sprawdza, czy lista dozwolonych IP blokuje żądania do /api/v1/admin/."""
    response = client.get('/api/v1/admin/dashboard/', REMOTE_ADDR='198.51.100.1')
    assert response.status_code == 404


