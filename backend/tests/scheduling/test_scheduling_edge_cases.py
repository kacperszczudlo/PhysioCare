import pytest
from django.db import IntegrityError, connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework import status

from scheduling.models import Visit, VisitStatus


@pytest.mark.django_db
def test_create_overlapping_visit_for_same_therapist_raises_integrity_error(
    patient, therapist, therapy_type
):
    from django.db import transaction

    # Arrange
    now = timezone.now()
    start_at = now + timezone.timedelta(hours=2)
    end_at = start_at + timezone.timedelta(minutes=45)

    Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=start_at,
        end_at=end_at,
        status=VisitStatus.SCHEDULED,
    )

    # Act & Assert - Attempt to create an overlapping visit inside atomic savepoint
    with transaction.atomic(), pytest.raises(IntegrityError):
        Visit.objects.create(
            patient=patient,
            therapist=therapist,
            therapy_type=therapy_type,
            start_at=start_at + timezone.timedelta(minutes=15),
            end_at=end_at + timezone.timedelta(minutes=15),
            status=VisitStatus.SCHEDULED,
        )


@pytest.mark.django_db
def test_adjacent_non_overlapping_visits_allowed(
    patient, therapist, therapy_type
):
    # Arrange
    now = timezone.now()
    v1_start = now + timezone.timedelta(hours=5)
    v1_end = v1_start + timezone.timedelta(minutes=45)
    v2_start = v1_end  # Touches exact end time of v1
    v2_end = v2_start + timezone.timedelta(minutes=45)

    # Act & Assert
    v1 = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=v1_start,
        end_at=v1_end,
        status=VisitStatus.SCHEDULED,
    )
    v2 = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=v2_start,
        end_at=v2_end,
        status=VisitStatus.SCHEDULED,
    )

    assert v1.id != v2.id
    assert Visit.objects.filter(therapist=therapist).count() == 2


@pytest.mark.django_db
def test_therapist_calendar_queries_are_optimized(api_client, therapist, patient, therapy_type):
    # Arrange
    now = timezone.now()
    for i in range(5):
        Visit.objects.create(
            patient=patient,
            therapist=therapist,
            therapy_type=therapy_type,
            start_at=now + timezone.timedelta(hours=i * 2 + 1),
            end_at=now + timezone.timedelta(hours=i * 2 + 1, minutes=45),
            status=VisitStatus.SCHEDULED,
        )

    api_client.force_authenticate(user=therapist.user)

    # Act
    with CaptureQueriesContext(connection) as context:
        response = api_client.get('/api/v1/therapist/visits/')

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert len(context.captured_queries) <= 4
