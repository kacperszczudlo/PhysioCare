import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from patients.models import PatientProfile
from privacy.account_deletion import anonymize_user_for_deletion

User = get_user_model()


@pytest.mark.django_db
def test_therapist_sees_only_own_patients(therapist, therapist_b, patient_profiles):
    user_b = therapist_b.user
    for index in range(1, 4):
        user = User.objects.create_user(
            email=f'otherpatient{index}@physiocare.test',
            password='test-pass',
            role='PATIENT',
            first_name='Inny',
            last_name=f'Pacjent{index}',
        )
        PatientProfile.objects.create(user=user, therapist=therapist_b)

    client = APIClient()
    client.force_authenticate(user=therapist.user)
    response = client.get('/api/v1/patients/')

    assert response.status_code == 200
    assert response.data['count'] == 10
    emails = {item['email'] for item in response.data['results']}
    assert all('otherpatient' not in email for email in emails)

    client.force_authenticate(user=user_b)
    response_b = client.get('/api/v1/patients/')
    assert response_b.data['count'] == 3


@pytest.mark.django_db
def test_patient_list_uses_select_related(therapist, patient_profiles):
    client = APIClient()
    client.force_authenticate(user=therapist.user)

    with CaptureQueriesContext(connection) as context:
        response = client.get('/api/v1/patients/')

    assert response.status_code == 200
    assert len(context.captured_queries) <= 3


@pytest.mark.django_db
def test_patient_list_excludes_soft_deleted_accounts(therapist, patient, api_client):
    anonymize_user_for_deletion(patient.user, source='user_request')

    api_client.force_authenticate(user=therapist.user)
    response = api_client.get('/api/v1/patients/')

    assert response.status_code == 200
    assert response.data['count'] == 0
    assert response.data['results'] == []


@pytest.mark.django_db
def test_dashboard_stats_exclude_soft_deleted_patients(
    therapist, patient, patient_profiles, api_client
):
    anonymize_user_for_deletion(patient.user, source='user_request')

    api_client.force_authenticate(user=therapist.user)
    response = api_client.get('/api/v1/therapist/dashboard/stats/')

    assert response.status_code == 200
    # patient_profiles fixture adds 10 active patients; soft-deleted `patient` is excluded
    assert response.data['patients_total'] == 10
