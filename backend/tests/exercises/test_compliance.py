from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from exercises.models import Exercise, ExerciseAssignment, ExerciseCompletion, MediaType


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
def test_patient_completes_assigned_exercise(
    api_client: object, patient: object, assignment: ExerciseAssignment,
) -> None:
    """Sprawdza oznaczanie wykonania przypisanego ćwiczenia przez pacjenta."""
    # Arrange
    api_client.force_authenticate(user=patient.user)

    today_response: object = api_client.get('/api/v1/me/exercises/today/')
    # Assert
    assert today_response.status_code == status.HTTP_200_OK
    assert today_response.data['count'] == 1
    assert today_response.data['results'][0]['id'] == str(assignment.id)
    assert today_response.data['results'][0]['completed_today'] is False
    assert 'categories' in today_response.data['results'][0]
    assert today_response.data['results'][0]['categories'] == []

    complete_response: object = api_client.post(
        '/api/v1/me/exercise-completions/',
        {'assignment_id': str(assignment.id), 'done': True},
        format='json',
    )

    assert complete_response.status_code == status.HTTP_201_CREATED
    assert complete_response.data['done'] is True
    assert ExerciseCompletion.objects.filter(assignment=assignment, done=True).count() == 1

    today_after: object = api_client.get('/api/v1/me/exercises/today/')
    assert today_after.data['results'][0]['completed_today'] is True


@pytest.mark.django_db
def test_patient_can_uncheck_exercise_completion(
    api_client: object, patient: object, assignment: ExerciseAssignment,
) -> None:
    """Sprawdza możliwość cofnięcia wykonania ćwiczenia przez pacjenta."""
    # Arrange
    api_client.force_authenticate(user=patient.user)

    first: object = api_client.post(
        '/api/v1/me/exercise-completions/',
        {'assignment_id': str(assignment.id), 'done': True},
        format='json',
    )
    # Assert
    assert first.status_code == status.HTTP_201_CREATED

    uncheck: object = api_client.post(
        '/api/v1/me/exercise-completions/',
        {'assignment_id': str(assignment.id), 'done': False},
        format='json',
    )
    assert uncheck.status_code == status.HTTP_200_OK
    assert uncheck.data['done'] is False
    assert ExerciseCompletion.objects.filter(assignment=assignment).count() == 1
    assert ExerciseCompletion.objects.get(assignment=assignment).done is False

    today_response: object = api_client.get('/api/v1/me/exercises/today/')
    assert today_response.data['results'][0]['completed_today'] is False


@pytest.mark.django_db
def test_completion_respects_valid_past_completed_on_for_offline_sync(
    api_client: object, patient: object, assignment: ExerciseAssignment,
) -> None:
    """Sprawdza, czy poprawna data przeszła z kolejki offline jest respektowana przez backend."""
    # Arrange
    api_client.force_authenticate(user=patient.user)
    today: object = timezone.localdate()
    yesterday: object = today - timedelta(days=1)
    client_skewed: str = yesterday.isoformat()

    response: object = api_client.post(
        '/api/v1/me/exercise-completions/',
        {'assignment_id': str(assignment.id), 'completed_on': client_skewed, 'done': True},
        format='json',
    )
    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['completed_on'] == client_skewed
    assert ExerciseCompletion.objects.filter(
        assignment=assignment,
        completed_on=yesterday,
        done=True,
    ).exists()


@pytest.mark.django_db
def test_completion_defaults_to_today_when_completed_on_omitted(
    api_client: object, patient: object, assignment: ExerciseAssignment,
) -> None:
    """Sprawdza, czy przy braku parametru completed_on domyślnie używana jest dzisiejsza data serwera."""
    # Arrange
    api_client.force_authenticate(user=patient.user)
    today: object = timezone.localdate()

    response: object = api_client.post(
        '/api/v1/me/exercise-completions/',
        {'assignment_id': str(assignment.id), 'done': True},
        format='json',
    )
    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['completed_on'] == today.isoformat()


@pytest.mark.django_db
def test_completion_rejects_future_completed_on(
    api_client: object, patient: object, assignment: ExerciseAssignment,
) -> None:
    """Sprawdza odrzucenie zapisu wykonania z datą w przyszłości."""
    # Arrange
    api_client.force_authenticate(user=patient.user)
    tomorrow: str = (timezone.localdate() + timedelta(days=1)).isoformat()

    response: object = api_client.post(
        '/api/v1/me/exercise-completions/',
        {'assignment_id': str(assignment.id), 'completed_on': tomorrow, 'done': True},
        format='json',
    )
    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_completion_rejects_completed_on_outside_assignment_range(
    api_client: object, patient: object, assignment: ExerciseAssignment,
) -> None:
    """Sprawdza odrzucenie wykonania z datą wykraczającą poza okres przypisania."""
    # Arrange
    api_client.force_authenticate(user=patient.user)
    too_early: str = (timezone.localdate() - timedelta(days=5)).isoformat()

    response: object = api_client.post(
        '/api/v1/me/exercise-completions/',
        {'assignment_id': str(assignment.id), 'completed_on': too_early, 'done': True},
        format='json',
    )
    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error']['code'] == 'VALIDATION'


@pytest.mark.django_db
def test_duplicate_exercise_completion_updates_existing(
    api_client: object, patient: object, assignment: ExerciseAssignment,
) -> None:
    """Sprawdza, czy powtórny wpis wykonania ćwiczenia aktualizuje istniejący rekord zamiast go duplikować."""
    # Arrange
    api_client.force_authenticate(user=patient.user)

    first: object = api_client.post(
        '/api/v1/me/exercise-completions/',
        {'assignment_id': str(assignment.id), 'done': True},
        format='json',
    )
    # Assert
    assert first.status_code == status.HTTP_201_CREATED

    second: object = api_client.post(
        '/api/v1/me/exercise-completions/',
        {'assignment_id': str(assignment.id), 'done': True},
        format='json',
    )
    assert second.status_code == status.HTTP_200_OK
    assert second.data['done'] is True
    assert ExerciseCompletion.objects.filter(assignment=assignment).count() == 1


@pytest.mark.django_db
def test_patient_lists_full_exercise_plan_with_history(
    api_client: object, patient: object, assignment: ExerciseAssignment, exercise: Exercise,
) -> None:
    """Sprawdza pobieranie pełnego planu ćwiczeń pacjenta z filtrowaniem wg scope (active/past)."""
    # Arrange
    today: object = timezone.localdate()
    past: ExerciseAssignment = ExerciseAssignment.objects.create(
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
    all_resp: object = api_client.get('/api/v1/me/exercises/')
    # Assert
    assert all_resp.status_code == status.HTTP_200_OK
    assert all_resp.data['count'] == 2
    active_row: dict[str, object] = next(r for r in all_resp.data['results'] if r['id'] == str(assignment.id))
    assert active_row['is_active'] is True
    assert active_row['completed_today'] is True
    assert len(active_row['completions']) == 1

    active_resp: object = api_client.get('/api/v1/me/exercises/?scope=active')
    assert active_resp.data['count'] == 1
    assert active_resp.data['results'][0]['id'] == str(assignment.id)

    past_resp: object = api_client.get('/api/v1/me/exercises/?scope=past')
    assert past_resp.data['count'] == 1
    assert past_resp.data['results'][0]['id'] == str(past.id)
