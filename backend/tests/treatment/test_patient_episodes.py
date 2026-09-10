from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from scheduling.models import Visit, VisitStatus
from treatment.models import TreatmentEpisode, VisitNote


@pytest.mark.django_db
def test_patient_lists_own_episodes(api_client, patient, therapist):
    episode = TreatmentEpisode.objects.create(
        patient=patient,
        icd10_code='M54.5',
        functional_diagnosis='Ograniczenie zgięcia lędźwiowego',
        summary_note='Pracujemy nad mobilnością i siłą.',
    )
    VisitNote.objects.create(episode=episode, content='Notatka kliniczna - ukryta')

    api_client.force_authenticate(user=patient.user)
    response = api_client.get('/api/v1/me/episodes/')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1
    row = response.data['results'][0]
    assert row['id'] == str(episode.id)
    assert row['functional_diagnosis'] == 'Ograniczenie zgięcia lędźwiowego'
    assert row['summary_note'] == 'Pracujemy nad mobilnością i siłą.'
    assert row['status_label'] == 'W trakcie'
    assert 'content' not in row

    detail = api_client.get(f'/api/v1/me/episodes/{episode.id}/')
    assert detail.status_code == status.HTTP_200_OK
    assert detail.data['icd10_code'] == 'M54.5'


@pytest.mark.django_db
def test_patient_cannot_see_other_patient_episode(
    api_client, patient, therapist_b,
):
    other_user = patient.user.__class__.objects.create_user(
        email='other-ep@physiocare.test',
        password='test-pass',
        role='PATIENT',
        first_name='Inny',
        last_name='Pacjent',
    )
    from patients.models import PatientProfile

    other = PatientProfile.objects.create(user=other_user, therapist=therapist_b)
    episode = TreatmentEpisode.objects.create(patient=other, summary_note='Cudzy')

    api_client.force_authenticate(user=patient.user)
    assert api_client.get('/api/v1/me/episodes/').data['count'] == 0
    assert api_client.get(f'/api/v1/me/episodes/{episode.id}/').status_code == 404


@pytest.mark.django_db
def test_therapist_cannot_list_me_episodes(api_client, therapist):
    api_client.force_authenticate(user=therapist.user)
    assert api_client.get('/api/v1/me/episodes/').status_code == 403


@pytest.mark.django_db
def test_patient_sees_visit_summary_in_inbox_and_visit_detail(
    api_client, patient, therapist, therapy_type,
):
    visit = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=timezone.now() - timedelta(days=1),
        end_at=timezone.now() - timedelta(days=1) + timedelta(minutes=45),
        status=VisitStatus.COMPLETED,
        patient_summary='',
    )

    api_client.force_authenticate(user=therapist.user)
    patch = api_client.patch(
        f'/api/v1/therapist/visits/{visit.id}/',
        {
            'patient_summary': 'Dziś pracowaliśmy nad biodrem. Kontynuuj ćwiczenia mostka 3×10.',
            'status': VisitStatus.COMPLETED,
        },
        format='json',
    )
    assert patch.status_code == status.HTTP_200_OK
    assert 'mostka' in patch.data['patient_summary']

    api_client.force_authenticate(user=patient.user)
    inbox = api_client.get('/api/v1/me/clinical-documents/?kind=visit_summary')
    assert inbox.status_code == status.HTTP_200_OK
    assert inbox.data['count'] == 1
    assert inbox.data['results'][0]['kind'] == 'visit_summary'
    assert 'mostka' in inbox.data['results'][0]['details']['patient_summary']

    detail = api_client.get(f'/api/v1/visits/{visit.id}/')
    assert detail.status_code == status.HTTP_200_OK
    assert 'biodrem' in detail.data['patient_summary']
