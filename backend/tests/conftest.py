import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from exercises.models import Exercise, ExerciseAssignment, ExerciseCompletion
from patients.models import PatientProfile
from scheduling.models import TherapyType, Visit
from therapists.models import TherapistProfile
from treatment.models import (
    DiagnosticRecommendation,
    MedicalDeviceOrder,
    PhysicianOrderRefusal,
    ReceptaNaRuchReferral,
    TreatmentEpisode,
)

User = get_user_model()


@pytest.fixture(scope='session')
def django_db_setup(django_db_blocker, django_db_use_migrations):
    with django_db_blocker.unblock():
        if django_db_use_migrations:
            call_command('migrate', verbosity=0)


@pytest.fixture(autouse=True)
def cleanup_test_data(db):
    yield
    ExerciseCompletion.objects.filter(
        assignment__patient__user__email__endswith='@physiocare.test',
    ).delete()
    ExerciseAssignment.objects.filter(
        patient__user__email__endswith='@physiocare.test',
    ).delete()
    Exercise.objects.filter(therapist__user__email__endswith='@physiocare.test').delete()
    MedicalDeviceOrder.objects.filter(
        patient__user__email__endswith='@physiocare.test',
    ).delete()
    DiagnosticRecommendation.objects.filter(
        episode__patient__user__email__endswith='@physiocare.test',
    ).delete()
    PhysicianOrderRefusal.objects.filter(
        episode__patient__user__email__endswith='@physiocare.test',
    ).delete()
    ReceptaNaRuchReferral.objects.filter(
        patient__user__email__endswith='@physiocare.test',
    ).delete()
    TreatmentEpisode.objects.filter(
        patient__user__email__endswith='@physiocare.test',
    ).delete()
    Visit.objects.filter(patient__user__email__endswith='@physiocare.test').delete()
    TherapyType.objects.filter(therapist__user__email__endswith='@physiocare.test').delete()
    PatientProfile.objects.filter(user__email__endswith='@physiocare.test').delete()
    TherapistProfile.objects.filter(user__email__endswith='@physiocare.test').delete()
    User.objects.filter(email__endswith='@physiocare.test').delete()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def therapist(db):
    user = User.objects.create_user(
        email='therapist@physiocare.test',
        password='test-pass',
        role='THERAPIST',
        first_name='Jan',
        last_name='Kowalski',
        email_verified_at=timezone.now(),
    )
    return TherapistProfile.objects.create(
        user=user,
        pwzf_number='71239',
    )


@pytest.fixture
def therapist_b(db):
    user = User.objects.create_user(
        email='therapistb@physiocare.test',
        password='test-pass',
        role='THERAPIST',
        first_name='Anna',
        last_name='Nowak',
        email_verified_at=timezone.now(),
    )
    return TherapistProfile.objects.create(
        user=user,
        pwzf_number='71240',
    )


@pytest.fixture
def therapy_type(therapist):
    return TherapyType.objects.create(
        therapist=therapist,
        name='Fizjoterapia',
    )


@pytest.fixture
def patient(db, therapist):
    user = User.objects.create_user(
        email='patient@physiocare.test',
        password='test-pass',
        role='PATIENT',
        first_name='Pacjent',
        last_name='Testowy',
        email_verified_at=timezone.now(),
    )
    return PatientProfile.objects.create(
        user=user,
        therapist=therapist,
    )


@pytest.fixture
def patient_profiles(db, therapist):
    patients = []
    for index in range(1, 11):
        user = User.objects.create_user(
            email=f'patient{index}@physiocare.test',
            password='test-pass',
            role='PATIENT',
            first_name=f'Pacjent{index}',
            last_name='Testowy',
            email_verified_at=timezone.now(),
        )
        patients.append(
            PatientProfile.objects.create(
                user=user,
                therapist=therapist,
            )
        )
    return patients
