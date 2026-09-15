from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from exercises.models import Exercise, ExerciseAssignment
from notifications.models import NotificationDelivery
from scheduling.models import Visit, VisitStatus


@pytest.mark.django_db
def test_notify_today_exercises_command_real_execution(patient, therapist):
    # Arrange
    ExerciseAssignment.objects.all().delete()
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
    assert NotificationDelivery.objects.filter(user=patient.user, pref_key='exercise_reminder').exists()


@pytest.mark.django_db
def test_notify_upcoming_visits_command_real_execution(
    patient, therapist, therapy_type
):
    # Arrange
    now = timezone.now()
    Visit.objects.create(
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
    assert NotificationDelivery.objects.filter(user=patient.user, pref_key='visit_reminder').exists()

