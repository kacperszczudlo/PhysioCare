import pytest
from django.utils import timezone

from accounts.models import CustomUser, RoleChoices
from patients.models import PatientProfile
from scheduling.models import TherapyType, Visit, VisitStatus
from scheduling.selectors import (
    therapist_availability_slots_selector,
    visit_list_for_patient_selector,
    visit_list_for_therapist_selector,
)
from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_scheduling_selectors_querysets_and_filters():
    u_t = CustomUser.objects.create_user(
        email='t_sel_sc@test.pl',
        password='password123!',
        role=RoleChoices.THERAPIST,
        first_name='T',
        last_name='S',
    )
    therapist = TherapistProfile.objects.create(user=u_t)

    u_p = CustomUser.objects.create_user(
        email='p_sel_sc@test.pl',
        password='password123!',
        role=RoleChoices.PATIENT,
        first_name='P',
        last_name='S',
    )
    patient = PatientProfile.objects.create(user=u_p)

    tt = TherapyType.objects.create(
        therapist=therapist,
        name='Konsultacja',
        duration_min=30,
    )

    now = timezone.now()
    Visit.objects.create(
        therapist=therapist,
        patient=patient,
        therapy_type=tt,
        start_at=now + timezone.timedelta(days=1),
        end_at=now + timezone.timedelta(days=1, minutes=30),
        status=VisitStatus.SCHEDULED,
    )

    t_visits = visit_list_for_therapist_selector(therapist)
    assert t_visits.count() == 1
    assert t_visits.first().therapy_type.name == 'Konsultacja'

    p_visits = visit_list_for_patient_selector(patient)
    assert p_visits.count() == 1

    slots = therapist_availability_slots_selector(therapist)
    assert slots.count() == 0
