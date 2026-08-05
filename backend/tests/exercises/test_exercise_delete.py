from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from exercises.models import Exercise, ExerciseAssignment, MediaType


@pytest.fixture
def exercise(therapist):
    return Exercise.objects.create(
        therapist=therapist,
        title='Mostek',
        media_type=MediaType.VIDEO,
        file_url='/media/exercises/mostek.mp4',
        instruction='Unieś biodra, utrzymaj 5 s.',
    )


@pytest.fixture
def assignment(exercise, patient):
    today = timezone.localdate()
    return ExerciseAssignment.objects.create(
        exercise=exercise,
        patient=patient,
        dosage='3x10',
        start_date=today - timedelta(days=1),
        end_date=today + timedelta(days=7),
    )


@pytest.mark.django_db
def test_therapist_can_delete_own_exercise(api_client, therapist, exercise, assignment):
    api_client.force_authenticate(user=therapist.user)

    response = api_client.delete(f'/api/v1/therapist/exercises/{exercise.id}/')

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Exercise.objects.filter(pk=exercise.id).exists()
    assert not ExerciseAssignment.objects.filter(pk=assignment.id).exists()


@pytest.mark.django_db
def test_therapist_cannot_delete_foreign_exercise(api_client, therapist_b, exercise):
    api_client.force_authenticate(user=therapist_b.user)

    response = api_client.delete(f'/api/v1/therapist/exercises/{exercise.id}/')

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert Exercise.objects.filter(pk=exercise.id).exists()


@pytest.mark.django_db
def test_therapist_can_retrieve_own_exercise(api_client, therapist, exercise):
    api_client.force_authenticate(user=therapist.user)

    response = api_client.get(f'/api/v1/therapist/exercises/{exercise.id}/')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == str(exercise.id)
    assert response.data['title'] == 'Mostek'


@pytest.mark.django_db
def test_therapist_can_update_exercise_metadata(api_client, therapist, exercise):
    api_client.force_authenticate(user=therapist.user)

    response = api_client.patch(
        f'/api/v1/therapist/exercises/{exercise.id}/',
        {
            'title': 'Mostek — progresja',
            'instruction': 'Unieś biodra wyżej.',
            'media_type': MediaType.VIDEO,
            'has_categories': '1',
        },
        format='multipart',
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data['title'] == 'Mostek — progresja'
    assert response.data['instruction'] == 'Unieś biodra wyżej.'
    exercise.refresh_from_db()
    assert exercise.title == 'Mostek — progresja'
    assert exercise.file_url == '/media/exercises/mostek.mp4'
