from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from exercises.models import Exercise, ExerciseAssignment, MediaType


@pytest.fixture
def exercise(therapist: object) -> Exercise:
    """Tworzy testowe ćwiczenie dla fizjoterapeuty."""
    return Exercise.objects.create(
        therapist=therapist,
        title='Mostek',
        media_type=MediaType.VIDEO,
        file_url='/media/exercises/mostek.mp4',
        instruction='Unieś biodra, utrzymaj 5 s.',
    )


@pytest.fixture
def assignment(exercise: Exercise, patient: object) -> ExerciseAssignment:
    """Tworzy testowe przypisanie ćwiczenia dla pacjenta."""
    today: object = timezone.localdate()
    return ExerciseAssignment.objects.create(
        exercise=exercise,
        patient=patient,
        dosage='3x10',
        start_date=today - timedelta(days=1),
        end_date=today + timedelta(days=7),
    )


@pytest.mark.django_db
def test_therapist_can_delete_own_exercise(
    api_client: object, therapist: object, exercise: Exercise, assignment: ExerciseAssignment,
) -> None:
    """Sprawdza usunięcie własnego ćwiczenia i kaskadowe usunięcie powiązanych przypisań."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)

    response: object = api_client.delete(f'/api/v1/therapist/exercises/{exercise.id}/')

    # Assert
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Exercise.objects.filter(pk=exercise.id).exists()
    assert not ExerciseAssignment.objects.filter(pk=assignment.id).exists()


@pytest.mark.django_db
def test_therapist_cannot_delete_foreign_exercise(
    api_client: object, therapist_b: object, exercise: Exercise,
) -> None:
    """Sprawdza odrzucenie próby usunięcia ćwiczenia innego fizjoterapeuty (BOLA)."""
    # Arrange
    api_client.force_authenticate(user=therapist_b.user)

    response: object = api_client.delete(f'/api/v1/therapist/exercises/{exercise.id}/')

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert Exercise.objects.filter(pk=exercise.id).exists()


@pytest.mark.django_db
def test_therapist_can_retrieve_own_exercise(
    api_client: object, therapist: object, exercise: Exercise,
) -> None:
    """Sprawdza pobranie szczegółów własnego ćwiczenia przez fizjoterapeutę."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)

    response: object = api_client.get(f'/api/v1/therapist/exercises/{exercise.id}/')

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == str(exercise.id)
    assert response.data['title'] == 'Mostek'


@pytest.mark.django_db
def test_therapist_can_update_exercise_metadata(
    api_client: object, therapist: object, exercise: Exercise,
) -> None:
    """Sprawdza aktualizację metadanych ćwiczenia (tytuł, instrukcja) przez fizjoterapeutę."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)

    response: object = api_client.patch(
        f'/api/v1/therapist/exercises/{exercise.id}/',
        {
            'title': 'Mostek - progresja',
            'instruction': 'Unieś biodra wyżej.',
            'media_type': MediaType.VIDEO,
            'has_categories': '1',
        },
        format='multipart',
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.data['title'] == 'Mostek - progresja'
    assert response.data['instruction'] == 'Unieś biodra wyżej.'
    exercise.refresh_from_db()
    assert exercise.title == 'Mostek - progresja'
    assert exercise.file_url == '/media/exercises/mostek.mp4'

