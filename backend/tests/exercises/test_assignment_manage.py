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
        instruction='Unieś biodra.',
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
def test_list_assignments_filtered_by_patient(api_client, therapist, assignment, patient):
    api_client.force_authenticate(user=therapist.user)

    response = api_client.get(
        f'/api/v1/therapist/exercise-assignments/?patient={patient.id}',
    )

    assert response.status_code == status.HTTP_200_OK
    results = response.data['results'] if 'results' in response.data else response.data
    assert len(results) == 1
    assert results[0]['id'] == str(assignment.id)
    assert results[0]['exercise_instruction'] == 'Unieś biodra.'


@pytest.mark.django_db
def test_patch_assignment_period(api_client, therapist, assignment):
    api_client.force_authenticate(user=therapist.user)
    today = timezone.localdate()
    new_end = (today + timedelta(days=21)).isoformat()

    response = api_client.patch(
        f'/api/v1/therapist/exercise-assignments/{assignment.id}/',
        {'end_date': new_end, 'dosage': '4x12'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data['end_date'] == new_end
    assert response.data['dosage'] == '4x12'
    assignment.refresh_from_db()
    assert assignment.dosage == '4x12'


@pytest.mark.django_db
def test_delete_assignment(api_client, therapist, assignment):
    api_client.force_authenticate(user=therapist.user)

    response = api_client.delete(f'/api/v1/therapist/exercise-assignments/{assignment.id}/')

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not ExerciseAssignment.objects.filter(pk=assignment.id).exists()


@pytest.mark.django_db
def test_cannot_manage_foreign_assignment(api_client, therapist_b, assignment):
    api_client.force_authenticate(user=therapist_b.user)

    response = api_client.delete(f'/api/v1/therapist/exercise-assignments/{assignment.id}/')

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert ExerciseAssignment.objects.filter(pk=assignment.id).exists()
