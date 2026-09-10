from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from exercises.models import Exercise, ExerciseAssignment, ExerciseCompletion, MediaType


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
def test_patient_completes_assigned_exercise(api_client, patient, assignment):
    api_client.force_authenticate(user=patient.user)

    today_response = api_client.get('/api/v1/me/exercises/today/')
    assert today_response.status_code == status.HTTP_200_OK
    assert today_response.data['count'] == 1
    assert today_response.data['results'][0]['id'] == str(assignment.id)
    assert today_response.data['results'][0]['completed_today'] is False
    assert 'categories' in today_response.data['results'][0]
    assert today_response.data['results'][0]['categories'] == []

    complete_response = api_client.post(
        '/api/v1/me/exercise-completions/',
        {'assignment_id': str(assignment.id), 'done': True},
        format='json',
    )

    assert complete_response.status_code == status.HTTP_201_CREATED
    assert complete_response.data['done'] is True
    assert ExerciseCompletion.objects.filter(assignment=assignment, done=True).count() == 1

    today_after = api_client.get('/api/v1/me/exercises/today/')
    assert today_after.data['results'][0]['completed_today'] is True


@pytest.mark.django_db
def test_patient_can_uncheck_exercise_completion(api_client, patient, assignment):
    api_client.force_authenticate(user=patient.user)

    first = api_client.post(
        '/api/v1/me/exercise-completions/',
        {'assignment_id': str(assignment.id), 'done': True},
        format='json',
    )
    assert first.status_code == status.HTTP_201_CREATED

    uncheck = api_client.post(
        '/api/v1/me/exercise-completions/',
        {'assignment_id': str(assignment.id), 'done': False},
        format='json',
    )
    assert uncheck.status_code == status.HTTP_200_OK
    assert uncheck.data['done'] is False
    assert ExerciseCompletion.objects.filter(assignment=assignment).count() == 1
    assert ExerciseCompletion.objects.get(assignment=assignment).done is False

    today_response = api_client.get('/api/v1/me/exercises/today/')
    assert today_response.data['results'][0]['completed_today'] is False


@pytest.mark.django_db
def test_completion_uses_server_local_date_not_client_clock(api_client, patient, assignment):
    """Client completed_on must not desync from MeExercisesToday (clinic TZ)."""
    api_client.force_authenticate(user=patient.user)
    today = timezone.localdate()
    client_skewed = (today - timedelta(days=1)).isoformat()

    response = api_client.post(
        '/api/v1/me/exercise-completions/',
        {'assignment_id': str(assignment.id), 'completed_on': client_skewed, 'done': True},
        format='json',
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['completed_on'] == today.isoformat()
    assert ExerciseCompletion.objects.filter(
        assignment=assignment,
        completed_on=today,
        done=True,
    ).exists()

    today_after = api_client.get('/api/v1/me/exercises/today/')
    assert today_after.data['results'][0]['completed_today'] is True


@pytest.mark.django_db
def test_duplicate_exercise_completion_updates_existing(api_client, patient, assignment):
    api_client.force_authenticate(user=patient.user)

    first = api_client.post(
        '/api/v1/me/exercise-completions/',
        {'assignment_id': str(assignment.id), 'done': True},
        format='json',
    )
    assert first.status_code == status.HTTP_201_CREATED

    second = api_client.post(
        '/api/v1/me/exercise-completions/',
        {'assignment_id': str(assignment.id), 'done': True},
        format='json',
    )
    assert second.status_code == status.HTTP_200_OK
    assert second.data['done'] is True
    assert ExerciseCompletion.objects.filter(assignment=assignment).count() == 1


@pytest.mark.django_db
def test_patient_lists_full_exercise_plan_with_history(api_client, patient, assignment, exercise):
    today = timezone.localdate()
    past = ExerciseAssignment.objects.create(
        exercise=exercise,
        patient=patient,
        dosage='2x8',
        start_date=today - timedelta(days=30),
        end_date=today - timedelta(days=10),
    )
    ExerciseCompletion.objects.create(
        assignment=assignment,
        completed_on=today,
        done=True,
    )

    api_client.force_authenticate(user=patient.user)
    all_resp = api_client.get('/api/v1/me/exercises/')
    assert all_resp.status_code == status.HTTP_200_OK
    assert all_resp.data['count'] == 2
    active_row = next(r for r in all_resp.data['results'] if r['id'] == str(assignment.id))
    assert active_row['is_active'] is True
    assert active_row['completed_today'] is True
    assert len(active_row['completions']) == 1

    active_resp = api_client.get('/api/v1/me/exercises/?scope=active')
    assert active_resp.data['count'] == 1
    assert active_resp.data['results'][0]['id'] == str(assignment.id)

    past_resp = api_client.get('/api/v1/me/exercises/?scope=past')
    assert past_resp.data['count'] == 1
    assert past_resp.data['results'][0]['id'] == str(past.id)
