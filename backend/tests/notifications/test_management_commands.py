from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.utils import timezone
import pytest

from exercises.models import Exercise, ExerciseAssignment
from scheduling.models import Visit, VisitStatus


@pytest.mark.django_db
@patch('notifications.management.commands.notify_today_exercises.notify_today_exercises')
def test_notify_today_exercises_command(
    mock_notify, patient, therapist
):
    # Arrange
    exercise = Exercise.objects.create(
        therapist=therapist,
        title='Rozciąganie',
    )
    today = timezone.localdate()
    ExerciseAssignment.objects.create(
        patient=patient,
        exercise=exercise,
        dosage='3x10',
        start_date=today,
        end_date=today,
    )
    out = StringIO()

    # Act
    call_command('notify_today_exercises', stdout=out)

    # Assert
    assert 'Przypomnienia o ćwiczeniach: 1' in out.getvalue()
    mock_notify.assert_called_once()


@pytest.mark.django_db
@patch('notifications.management.commands.notify_upcoming_visits.notify_visit_reminder')
def test_notify_upcoming_visits_command(
    mock_notify, patient, therapist, therapy_type
):
    # Arrange
    now = timezone.now()
    visit = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=now + timezone.timedelta(hours=24),
        end_at=now + timezone.timedelta(hours=24, minutes=45),
        status=VisitStatus.SCHEDULED,
    )
    out = StringIO()

    # Act
    call_command('notify_upcoming_visits', stdout=out)

    # Assert
    assert 'Przypomnienia zakolejkowane:' in out.getvalue()
    mock_notify.assert_called_once_with(visit, '24h')
