import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from patients.models import PatientProfile
from privacy.account_deletion import anonymize_user_for_deletion

User: object = get_user_model()


@pytest.mark.django_db
def test_therapist_sees_only_own_patients(
    therapist: object, therapist_b: object, patient_profiles: object,
) -> None:
    """Sprawdza, czy fizjoterapeuta widzi na liście wyłącznie przypisanych do siebie pacjentów (BOLA)."""
    # Arrange
    user_b: object = therapist_b.user
    for index in range(1, 4):
        user: object = User.objects.create_user(
            email=f'otherpatient{index}@physiocare.test',
            password='test-pass',
            role='PATIENT',
            first_name='Inny',
            last_name=f'Pacjent{index}',
        )
        PatientProfile.objects.create(user=user, therapist=therapist_b)

    client: APIClient = APIClient()
    client.force_authenticate(user=therapist.user)
    response: object = client.get('/api/v1/patients/')

    # Assert
    assert response.status_code == 200
    assert response.data['count'] == 10
    emails: set[str] = {item['email'] for item in response.data['results']}
    assert all('otherpatient' not in email for email in emails)

    client.force_authenticate(user=user_b)
    response_b: object = client.get('/api/v1/patients/')
    assert response_b.data['count'] == 3


@pytest.mark.django_db
def test_patient_list_uses_select_related(
    therapist: object, patient_profiles: object,
) -> None:
    """Sprawdza optymalizację zapytania SQL listy pacjentów pod kątem zapytań N+1."""
    # Arrange
    client: APIClient = APIClient()
    client.force_authenticate(user=therapist.user)

    # Act
    with CaptureQueriesContext(connection) as context:
        response: object = client.get('/api/v1/patients/')

    # Assert
    assert response.status_code == 200
    assert len(context.captured_queries) <= 3


@pytest.mark.django_db
def test_patient_list_excludes_soft_deleted_accounts(
    therapist: object, patient: object, api_client: object,
) -> None:
    """Sprawdza wykluczenie miękko usuniętych kont pacjentów z wyników wyszukiwania i list."""
    # Arrange
    anonymize_user_for_deletion(patient.user, source='user_request')

    api_client.force_authenticate(user=therapist.user)
    response: object = api_client.get('/api/v1/patients/')

    # Assert
    assert response.status_code == 200
    assert response.data['count'] == 0
    assert response.data['results'] == []


@pytest.mark.django_db
def test_dashboard_stats_exclude_soft_deleted_patients(
    therapist: object, patient: object, patient_profiles: object, api_client: object,
) -> None:
    """Sprawdza wykluczenie miękko usuniętych pacjentów z zagregowanych statystyk pulpitu nawigacyjnego."""
    # Arrange
    anonymize_user_for_deletion(patient.user, source='user_request')

    api_client.force_authenticate(user=therapist.user)
    response: object = api_client.get('/api/v1/therapist/dashboard/stats/')

    # Assert
    assert response.status_code == 200
    assert response.data['patients_total'] == 10

