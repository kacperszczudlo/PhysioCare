from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from scheduling.models import Visit, VisitStatus


@pytest.mark.django_db
def test_patient_can_request_visit(api_client, therapist, patient, therapy_type):
    api_client.force_authenticate(user=patient.user)
    start_at = timezone.now() + timedelta(days=2)
    end_at = start_at + timedelta(minutes=45)

    response = api_client.post(
        '/api/v1/me/visits/',
        {
            'therapy_type_id': str(therapy_type.id),
            'start_at': start_at.isoformat(),
            'end_at': end_at.isoformat(),
            'patient_note': 'Proszę o wizytę po południu',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['status'] == VisitStatus.PENDING_APPROVAL
    assert str(response.data['patient']) == str(patient.id)
    assert str(response.data['therapist']) == str(therapist.id)
    assert response.data['patient_note'] == 'Proszę o wizytę po południu'
    assert response.data['prep_instructions'] == ''
    assert Visit.objects.filter(patient=patient, status=VisitStatus.PENDING_APPROVAL).count() == 1


@pytest.mark.django_db
def test_patient_request_rejects_past_slot(api_client, patient, therapy_type):
    api_client.force_authenticate(user=patient.user)
    start_at = timezone.now() - timedelta(hours=1)
    end_at = start_at + timedelta(minutes=45)

    response = api_client.post(
        '/api/v1/me/visits/',
        {
            'therapy_type_id': str(therapy_type.id),
            'start_at': start_at.isoformat(),
            'end_at': end_at.isoformat(),
        },
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_therapist_can_approve_and_reject_request(
    api_client, therapist, patient, therapy_type,
):
    start_at = timezone.now() + timedelta(days=3)
    end_at = start_at + timedelta(minutes=45)
    visit = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=start_at,
        end_at=end_at,
        status=VisitStatus.PENDING_APPROVAL,
        location_address='Gabinet 1',
    )

    api_client.force_authenticate(user=therapist.user)
    approve = api_client.post(f'/api/v1/therapist/visits/{visit.id}/approve/', {}, format='json')
    assert approve.status_code == status.HTTP_200_OK
    assert approve.data['status'] == VisitStatus.SCHEDULED

    visit.refresh_from_db()
    visit.status = VisitStatus.PENDING_APPROVAL
    visit.save(update_fields=['status'])

    reject = api_client.post(
        f'/api/v1/therapist/visits/{visit.id}/reject/',
        {'cancel_reason': 'Brak wolnego terminu'},
        format='json',
    )
    assert reject.status_code == status.HTTP_200_OK
    assert reject.data['status'] == VisitStatus.CANCELLED
    assert 'Brak wolnego terminu' in reject.data['cancel_reason']


@pytest.mark.django_db
def test_pending_holds_slot_against_overlap(
    api_client, therapist, patient_profiles, therapy_type,
):
    start_at = timezone.now() + timedelta(days=4)
    end_at = start_at + timedelta(minutes=45)
    Visit.objects.create(
        patient=patient_profiles[0],
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=start_at,
        end_at=end_at,
        status=VisitStatus.PENDING_APPROVAL,
        location_address='Gabinet 1',
    )

    api_client.force_authenticate(user=patient_profiles[1].user)
    response = api_client.post(
        '/api/v1/me/visits/',
        {
            'therapy_type_id': str(therapy_type.id),
            'start_at': start_at.isoformat(),
            'end_at': end_at.isoformat(),
        },
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_upcoming_includes_pending_for_patient(api_client, therapist, patient, therapy_type):
    start_at = timezone.now() + timedelta(days=1)
    end_at = start_at + timedelta(minutes=45)
    Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=start_at,
        end_at=end_at,
        status=VisitStatus.PENDING_APPROVAL,
        location_address='Gabinet 1',
    )

    api_client.force_authenticate(user=patient.user)
    response = api_client.get('/api/v1/me/visits/?status=upcoming')
    assert response.status_code == status.HTTP_200_OK
    results = response.data.get('results', response.data)
    assert len(results) == 1
    assert results[0]['status'] == VisitStatus.PENDING_APPROVAL


@pytest.mark.django_db
def test_patient_can_list_therapist_therapy_types(api_client, patient, therapy_type):
    api_client.force_authenticate(user=patient.user)
    response = api_client.get('/api/v1/me/therapy-types/')
    assert response.status_code == status.HTTP_200_OK
    results = response.data.get('results', response.data)
    assert any(item['id'] == str(therapy_type.id) for item in results)


@pytest.mark.django_db
def test_therapist_upcoming_respects_limit(api_client, therapist, patient, therapy_type):
    base = timezone.now() + timedelta(hours=1)
    for i in range(7):
        start_at = base + timedelta(hours=i * 2)
        Visit.objects.create(
            patient=patient,
            therapist=therapist,
            therapy_type=therapy_type,
            start_at=start_at,
            end_at=start_at + timedelta(minutes=45),
            status=VisitStatus.SCHEDULED,
            location_address='Gabinet 1',
        )

    api_client.force_authenticate(user=therapist.user)
    response = api_client.get('/api/v1/therapist/visits/?upcoming=1&limit=5')
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) == 5
    starts = [item['start_at'] for item in response.data]
    assert starts == sorted(starts)
