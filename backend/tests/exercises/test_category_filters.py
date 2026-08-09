import pytest
from rest_framework import status

from exercises.models import CategoryKind, Exercise, ExerciseCategory, MediaType


@pytest.fixture
def categories(db):
    """Use seeded taxonomy when present; otherwise create a minimal set."""
    def ensure(kind, slug, name):
        cat, _ = ExerciseCategory.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'kind': kind},
        )
        if cat.kind != kind or cat.name != name:
            cat.kind = kind
            cat.name = name
            cat.save(update_fields=['kind', 'name'])
        return cat

    return {
        'type': ensure(CategoryKind.TYPE, 'strengthening', 'Wzmacnianie'),
        'region': ensure(CategoryKind.REGION, 'knee', 'Kolano'),
        'muscle': ensure(CategoryKind.MUSCLE, 'quadriceps', 'Czworogłowy uda'),
        'injury': ensure(CategoryKind.INJURY, 'acl_rehab', 'Po rekonstrukcji ACL'),
        'other_type': ensure(CategoryKind.TYPE, 'stretching', 'Rozciąganie'),
    }


@pytest.fixture
def catalog(therapist, categories):
    matched = Exercise.objects.create(
        therapist=therapist,
        title='Squat izometryczny',
        media_type=MediaType.VIDEO,
        file_url='/media/exercises/squat.mp4',
        instruction='Utrzymaj kąt 45°.',
    )
    matched.categories.set([
        categories['type'],
        categories['region'],
        categories['muscle'],
        categories['injury'],
    ])

    stretch_only = Exercise.objects.create(
        therapist=therapist,
        title='Rozciąganie łydek',
        media_type=MediaType.PDF,
        file_url='/media/exercises/calf.pdf',
        instruction='30 s na stronę.',
    )
    stretch_only.categories.set([categories['other_type']])

    return {'matched': matched, 'stretch_only': stretch_only}


@pytest.mark.django_db
def test_list_categories_includes_kind_and_slug(api_client, therapist, categories):
    api_client.force_authenticate(user=therapist.user)

    response = api_client.get('/api/v1/therapist/exercise-categories/')

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) >= 5
    sample = next(item for item in response.data if item['slug'] == 'knee')
    assert sample['kind'] == CategoryKind.REGION
    assert sample['name'] == 'Kolano'


@pytest.mark.django_db
def test_list_categories_filter_by_kind(api_client, therapist, categories):
    api_client.force_authenticate(user=therapist.user)

    response = api_client.get('/api/v1/therapist/exercise-categories/?kind=MUSCLE')

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) >= 1
    assert all(item['kind'] == CategoryKind.MUSCLE for item in response.data)
    assert any(item['slug'] == 'quadriceps' for item in response.data)


@pytest.mark.django_db
def test_filter_exercises_by_typed_slugs(api_client, therapist, catalog):
    api_client.force_authenticate(user=therapist.user)

    response = api_client.get(
        '/api/v1/therapist/exercises/?type=strengthening&region=knee&muscle=quadriceps&injury=acl_rehab',
    )

    assert response.status_code == status.HTTP_200_OK
    results = response.data['results'] if isinstance(response.data, dict) else response.data
    ids = {item['id'] for item in results}
    assert str(catalog['matched'].id) in ids
    assert str(catalog['stretch_only'].id) not in ids


@pytest.mark.django_db
def test_filter_exercises_and_across_kinds(api_client, therapist, catalog):
    api_client.force_authenticate(user=therapist.user)

    response = api_client.get('/api/v1/therapist/exercises/?type=stretching&region=knee')

    assert response.status_code == status.HTTP_200_OK
    results = response.data['results'] if isinstance(response.data, dict) else response.data
    assert results == []


@pytest.mark.django_db
def test_filter_exercises_by_category_slug(api_client, therapist, catalog):
    api_client.force_authenticate(user=therapist.user)

    response = api_client.get('/api/v1/therapist/exercises/?category=stretching')

    assert response.status_code == status.HTTP_200_OK
    results = response.data['results'] if isinstance(response.data, dict) else response.data
    ids = {item['id'] for item in results}
    assert str(catalog['stretch_only'].id) in ids
    assert str(catalog['matched'].id) not in ids


@pytest.mark.django_db
def test_search_includes_instruction(api_client, therapist, catalog):
    api_client.force_authenticate(user=therapist.user)

    response = api_client.get('/api/v1/therapist/exercises/?q=45°')

    assert response.status_code == status.HTTP_200_OK
    results = response.data['results'] if isinstance(response.data, dict) else response.data
    assert len(results) == 1
    assert results[0]['id'] == str(catalog['matched'].id)
