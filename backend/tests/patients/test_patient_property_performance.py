import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from accounts.models import CustomUser, RoleChoices
from patients.models import LinkStatus, PatientProfile, PatientTherapistLink
from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_patient_therapist_property_does_not_execute_uncached_query_if_prefetched():
    u1 = CustomUser.objects.create_user(
        email='p_perf@test.pl',
        password='password123!',
        role=RoleChoices.PATIENT,
        first_name='Jan',
        last_name='Kowalski',
    )
    patient = PatientProfile.objects.create(user=u1)
    u2 = CustomUser.objects.create_user(
        email='t_perf@test.pl',
        password='password123!',
        role=RoleChoices.THERAPIST,
        first_name='Adam',
        last_name='Nowak',
    )
    therapist = TherapistProfile.objects.create(user=u2)
    PatientTherapistLink.objects.create(
        patient=patient, therapist=therapist, status=LinkStatus.ACTIVE
    )

    # Pobieramy pacjenta z prefetch_related therapists
    p = PatientProfile.objects.prefetch_related('therapists').get(pk=patient.pk)
    with CaptureQueriesContext(connection) as ctx:
        _ = p.therapist_id
        # Nie powinno być dodatkowego zapytania SQL po prefetchu
        assert len(ctx.captured_queries) == 0
