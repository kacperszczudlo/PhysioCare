import os
import socket

import pytest
from django.contrib.auth import get_user_model

from patients.models import PatientProfile
from therapists.models import TherapistProfile

User = get_user_model()


def postgres_available() -> bool:
    host = os.environ.get('POSTGRES_HOST', 'localhost')
    port = int(os.environ.get('POSTGRES_PORT', '5432'))
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


requires_postgres = pytest.mark.skipif(
    not postgres_available(),
    reason='PostgreSQL is required for ExclusionConstraint tests',
)


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
