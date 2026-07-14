import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from patients.models import PatientProfile
from scheduling.models import Visit
from therapists.models import TherapistProfile

User = get_user_model()


@pytest.fixture(scope='session')
def django_db_setup(django_db_blocker, django_db_use_migrations):
    """
    Używa istniejącej bazy physiocare z .env.
    Nie wymaga CREATEDB (brak tworzenia test_physiocare).
    """
    with django_db_blocker.unblock():
        if django_db_use_migrations:
            call_command('migrate', verbosity=0)


@pytest.fixture(autouse=True)
def cleanup_test_data(db):
    yield
    Visit.objects.filter(patient__user__email__endswith='@physiocare.test').delete()
    PatientProfile.objects.filter(user__email__endswith='@physiocare.test').delete()
    TherapistProfile.objects.filter(user__email__endswith='@physiocare.test').delete()
    User.objects.filter(email__endswith='@physiocare.test').delete()


@pytest.fixture
def therapist(db):
    user = User.objects.create_user(
        email='therapist@physiocare.test',
        password='test-pass',
        role='THERAPIST',
    )
    return TherapistProfile.objects.create(
        user=user,
        first_name='Jan',
        last_name='Kowalski',
    )


@pytest.fixture
def patient_profiles(db):
    patients = []
    for index in range(1, 11):
        user = User.objects.create_user(
            email=f'patient{index}@physiocare.test',
            password='test-pass',
            role='PATIENT',
        )
        patients.append(
            PatientProfile.objects.create(
                user=user,
                first_name=f'Pacjent{index}',
                last_name='Testowy',
            )
        )
    return patients
