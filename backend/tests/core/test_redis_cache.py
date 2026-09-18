import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from exercises.models import CategoryKind, ExerciseCategory


@pytest.mark.django_db
def test_django_cache_get_set() -> None:
    """Sprawdza działanie podstawowego API pamięci podręcznej Django."""
    # Arrange
    cache.clear()
    key: str = "test_key_physiocare"
    value: dict[str, str] = {"status": "ok", "app": "PhysioCare"}

    # Act
    cache.set(key, value, timeout=60)
    retrieved: dict[str, str] | None = cache.get(key)

    # Assert
    assert retrieved == value
    cache.delete(key)
    assert cache.get(key) is None


@pytest.mark.django_db
def test_therapist_exercise_category_list_caching(therapist: object) -> None:
    """Sprawdza buforowanie odpowiedzi w widoku listy kategorii ćwiczeń."""
    # Arrange
    cache.clear()
    ExerciseCategory.objects.create(name="Rozciąganie kręgosłupa", kind=CategoryKind.REGION, slug="rozciaganie-kregoslupa")
    ExerciseCategory.objects.create(name="Trening siłowy", kind=CategoryKind.TYPE, slug="trening-silowy")

    client: APIClient = APIClient()
    client.force_authenticate(user=therapist.user)
    url: str = reverse("therapist-exercise-categories")

    # Act 1: Pierwsze zapytanie pobiera z bazy danych i zapisuje w cache
    response1 = client.get(url, {"kind": "REGION"})
    assert response1.status_code == status.HTTP_200_OK
    data1 = response1.json()
    assert len(data1) == 1
    assert data1[0]["name"] == "Rozciąganie kręgosłupa"

    # Weryfikacja obecności w cache
    cached_in_redis = cache.get("exercise_categories:REGION")
    assert cached_in_redis is not None
    assert len(cached_in_redis) == 1

    # Act 2: Drugie zapytanie powinno zwrócić zbuforowane dane
    response2 = client.get(url, {"kind": "REGION"})
    assert response2.status_code == status.HTTP_200_OK
    assert response2.json() == data1
