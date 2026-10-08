from collections.abc import Generator
from typing import TYPE_CHECKING

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from exercises.models import Exercise, ExerciseAssignment, ExerciseCompletion
from patients.models import PatientProfile
from reviews.models import Review
from scheduling.models import TherapyType, Visit
from therapists.models import TherapistProfile
from treatment.models import (
    DiagnosticRecommendation,
    MedicalDeviceOrder,
    PhysicianOrderRefusal,
    ReceptaNaRuchReferral,
    TreatmentEpisode,
)

if TYPE_CHECKING:
    from pytest_django.plugin import DjangoDbBlocker

User = get_user_model()


@pytest.fixture(scope='session')
def django_db_setup(
    django_db_blocker: 'DjangoDbBlocker',
    django_db_use_migrations: bool,
) -> None:
    """Konfiguruje bazę danych dla sesji testowej Pytest."""
    with django_db_blocker.unblock():
        if django_db_use_migrations:
            call_command('migrate', verbosity=0)


@pytest.fixture(autouse=True)
def cleanup_test_data(db: object) -> Generator[None, None, None]:
    """Automatyczna czyszcząca fixture usuwająca dane testowe po zakończeniu każdego testu."""
    yield
    Review.objects.filter(
        patient__user__email__endswith='@physiocare.test',
    ).delete()
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
    PatientProfile.objects.filter(user__email__endswith='@deleted.invalid').delete()
    TherapistProfile.objects.filter(user__email__endswith='@physiocare.test').delete()
    User.objects.filter(email__endswith='@physiocare.test').delete()
    User.objects.filter(email__endswith='@deleted.invalid').delete()


@pytest.fixture
def api_client() -> APIClient:
    """Tworzy instancję klienta API Django REST Framework do testowania endpointów."""
    return APIClient()


@pytest.fixture
def therapist(db: object) -> TherapistProfile:
    """Tworzy domyślny profil fizjoterapeuty z numerem PWZFz na potrzeby testów."""
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
def therapist_b(db: object) -> TherapistProfile:
    """Tworzy drugi profil fizjoterapeuty na potrzeby testowania uprawnień BOLA/AuthZ."""
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
def therapy_type(therapist: TherapistProfile) -> TherapyType:
    """Tworzy domyślny typ terapii powiązany z pierwszym fizjoterapeutą."""
    return TherapyType.objects.create(
        therapist=therapist,
        name='Fizjoterapia',
    )


@pytest.fixture
def patient(db: object, therapist: TherapistProfile) -> PatientProfile:
    """Tworzy profil pacjenta przypisanego do domyślnego fizjoterapeuty."""
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
def patient_profiles(db: object, therapist: TherapistProfile) -> list[PatientProfile]:
    """Tworzy zestaw 10 profili pacjentów na potrzeby testowania współbieżności i list."""
    patients: list[PatientProfile] = []
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


@pytest.fixture
def admin_user(db: object) -> User:
    """Tworzy użytkownika z rolą administratora na potrzeby testów."""
    return User.objects.create_superuser(
        email='admin@physiocare.test',
        password='test-pass',
        role='ADMIN',
        first_name='Admin',
        last_name='Główny',
        email_verified_at=timezone.now(),
    )

