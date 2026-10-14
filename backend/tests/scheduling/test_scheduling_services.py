from datetime import timedelta

import pytest
from django.utils import timezone

from accounts.models import CustomUser, RoleChoices
from patients.models import PatientProfile
from scheduling.models import TherapyType, Visit, VisitStatus
from scheduling.services import (
    visit_approve_service,
    visit_cancel_service,
    visit_create_service,
    visit_reschedule_service,
)
from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_visit_services_lifecycle():
    u_p = CustomUser.objects.create_user(
        email='p_sched_s@test.pl',
        password='password123!',
        role=RoleChoices.PATIENT,
        first_name='P',
        last_name='S',
    )
    patient = PatientProfile.objects.create(user=u_p)
    u_t = CustomUser.objects.create_user(
        email='t_sched_s@test.pl',
        password='password123!',
        role=RoleChoices.THERAPIST,
        first_name='T',
        last_name='S',
    )
    therapist = TherapistProfile.objects.create(user=u_t)
    tt = TherapyType.objects.create(
        therapist=therapist,
        name='Terapia manualna',
        duration_min=45,
    )

    start = timezone.now() + timedelta(days=2)
    end = start + timedelta(minutes=45)

    # 1. Tworzenie wizyty przez serwis
    visit = visit_create_service(
        therapist=therapist,
        patient=patient,
        therapy_type=tt,
        start_at=start,
        end_at=end,
    )
    assert visit.status == VisitStatus.SCHEDULED

    # 2. Przełożenie terminu
    new_start = start + timedelta(hours=2)
    new_end = end + timedelta(hours=2)
    rescheduled = visit_reschedule_service(
        visit=visit,
        new_start_at=new_start,
        new_end_at=new_end,
        requested_by_user=u_p,
    )
    assert rescheduled.start_at == new_start

    # 3. Odwołanie wizyty
    cancelled = visit_cancel_service(
        visit=rescheduled,
        cancelled_by_user=u_p,
        reason='Pilny wyjazd',
    )
    assert cancelled.status == VisitStatus.CANCELLED
    assert cancelled.cancel_reason == 'Pilny wyjazd'

    # 4. Zatwierdzenie wizyty oczekującej
    pending_visit = Visit.objects.create(
        therapist=therapist,
        patient=patient,
        therapy_type=tt,
        start_at=start + timedelta(days=5),
        end_at=end + timedelta(days=5),
        status=VisitStatus.PENDING_APPROVAL,
    )
    approved = visit_approve_service(visit=pending_visit, therapist=therapist)
    assert approved.status == VisitStatus.SCHEDULED
