from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from scheduling.models import Visit, VisitStatus


@pytest.mark.django_db
def test_valid_visit_status_lifecycle(therapist, patient, therapy_type):
    """Przejścia stanów: SCHEDULED -> COMPLETED oraz SCHEDULED -> CANCELLED."""
    now = timezone.now()
    visit = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=now + timedelta(days=1),
        end_at=now + timedelta(days=1, minutes=45),
        status=VisitStatus.SCHEDULED,
    )

    # Transition to COMPLETED
    visit.status = VisitStatus.COMPLETED
    visit.save()
    visit.refresh_from_db()
    assert visit.status == VisitStatus.COMPLETED

    # Create another visit for cancellation
    visit2 = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=now + timedelta(days=2),
        end_at=now + timedelta(days=2, minutes=45),
        status=VisitStatus.SCHEDULED,
    )
    visit2.status = VisitStatus.CANCELLED
    visit2.save()
    visit2.refresh_from_db()
    assert visit2.status == VisitStatus.CANCELLED


@pytest.mark.django_db
def test_cancel_visit_via_api(api_client, therapist, patient, therapy_type):
    """Anulowanie zaplanowanej wizyty przez API z użyciem dedykowanego endpointu."""
    now = timezone.now()
    visit = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=now + timedelta(days=1),
        end_at=now + timedelta(days=1, minutes=45),
        status=VisitStatus.SCHEDULED,
    )

    api_client.force_authenticate(user=therapist.user)
    response = api_client.post(
        f'/api/v1/visits/{visit.id}/cancel/',
        data={'reason': 'Pacjent odwołał wizytę telefonicznie'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    visit.refresh_from_db()
    assert visit.status == VisitStatus.CANCELLED


@pytest.mark.django_db
def test_cannot_cancel_already_cancelled_visit(api_client, therapist, patient, therapy_type):
    """Próba ponownego anulowania już odwołanej wizyty powinna zostać odrzucona (HTTP 400)."""
    now = timezone.now()
    visit = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=now + timedelta(days=1),
        end_at=now + timedelta(days=1, minutes=45),
        status=VisitStatus.CANCELLED,
    )

    api_client.force_authenticate(user=therapist.user)
    response = api_client.post(
        f'/api/v1/visits/{visit.id}/cancel/',
        data={'reason': 'Ponowna próba anulowania'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error']['code'] in ['INVALID', 'VALIDATION_ERROR', 'ALREADY_CANCELLED', 'VISIT_NOT_CANCELLABLE']
