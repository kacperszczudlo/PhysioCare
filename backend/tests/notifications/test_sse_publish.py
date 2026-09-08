from datetime import timedelta
from queue import Empty

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework import status

from exercises.models import Exercise, MediaType
from notifications.sse import get_sse_bus
from scheduling.models import Visit, VisitStatus


@pytest.fixture(autouse=True)
def _clear_sse_bus():
    get_sse_bus().clear()
    yield
    get_sse_bus().clear()


def _drain(queue, *, expected: int, timeout: float = 1.0) -> list:
    items = []
    for _ in range(expected):
        items.append(queue.get(timeout=timeout))
    with pytest.raises(Empty):
        queue.get(timeout=0.05)
    return items


@pytest.mark.django_db
def test_therapist_visit_create_publishes_sse_to_both(
    api_client,
    therapist,
    patient,
    therapy_type,
):
    patient_q = get_sse_bus().subscribe(str(patient.user_id))
    therapist_q = get_sse_bus().subscribe(str(therapist.user_id))
    api_client.force_authenticate(user=therapist.user)
    start_at = timezone.now() + timedelta(days=2)
    end_at = start_at + timedelta(minutes=45)

    response = api_client.post(
        '/api/v1/therapist/visits/',
        {
            'patient_id': str(patient.id),
            'therapy_type_id': str(therapy_type.id),
            'start_at': start_at.isoformat(),
            'end_at': end_at.isoformat(),
        },
        format='json',
    )
    assert response.status_code == status.HTTP_201_CREATED
    visit_id = response.data['id']

    for queue in (patient_q, therapist_q):
        events = _drain(queue, expected=1)
        assert events[0].type == 'visit.scheduled'
        assert events[0].resource_id == visit_id


@pytest.mark.django_db
def test_patient_visit_request_publishes_sse_without_email_side_effect(
    api_client,
    patient,
    therapy_type,
    settings,
):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    from django.core import mail

    mail.outbox.clear()

    therapist = patient.therapist
    patient_q = get_sse_bus().subscribe(str(patient.user_id))
    therapist_q = get_sse_bus().subscribe(str(therapist.user_id))
    api_client.force_authenticate(user=patient.user)
    start_at = timezone.now() + timedelta(days=2)
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
    assert response.status_code == status.HTTP_201_CREATED
    assert mail.outbox == []
    visit_id = response.data['id']

    for queue in (patient_q, therapist_q):
        events = _drain(queue, expected=1)
        assert events[0].type == 'visit.scheduled'
        assert events[0].resource_id == visit_id


@pytest.mark.django_db
def test_patient_cancel_publishes_sse_to_therapist(
    api_client,
    therapist,
    patient,
    therapy_type,
):
    visit = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=timezone.now() + timedelta(days=3),
        end_at=timezone.now() + timedelta(days=3, minutes=45),
        status=VisitStatus.SCHEDULED,
    )
    therapist_q = get_sse_bus().subscribe(str(therapist.user_id))
    patient_q = get_sse_bus().subscribe(str(patient.user_id))
    api_client.force_authenticate(user=patient.user)

    response = api_client.post(
        f'/api/v1/visits/{visit.id}/cancel/',
        {'cancel_reason': 'Konflikt'},
        format='json',
    )
    assert response.status_code == status.HTTP_200_OK

    for queue in (patient_q, therapist_q):
        events = _drain(queue, expected=1)
        assert events[0].type == 'visit.cancelled'
        assert events[0].resource_id == str(visit.id)


@pytest.mark.django_db
def test_exercise_assignment_publishes_sse_to_patient(
    api_client,
    therapist,
    patient,
):
    exercise = Exercise.objects.create(
        therapist=therapist,
        title='Mostek',
        media_type=MediaType.VIDEO,
        file_url='/media/exercises/mostek.mp4',
        instruction='Unieś biodra.',
    )
    patient_q = get_sse_bus().subscribe(str(patient.user_id))
    api_client.force_authenticate(user=therapist.user)
    today = timezone.localdate()

    response = api_client.post(
        '/api/v1/therapist/exercise-assignments/',
        {
            'exercise_id': str(exercise.id),
            'patient_id': str(patient.id),
            'dosage': '3x10',
            'start_date': today.isoformat(),
            'end_date': (today + timedelta(days=7)).isoformat(),
        },
        format='json',
    )
    assert response.status_code == status.HTTP_201_CREATED
    events = _drain(patient_q, expected=1)
    assert events[0].type == 'exercise.assigned'
    assert events[0].resource_id == response.data['id']


@pytest.mark.django_db
def test_document_upload_publishes_sse_to_patient(
    api_client,
    therapist,
    patient,
):
    patient_q = get_sse_bus().subscribe(str(patient.user_id))
    api_client.force_authenticate(user=therapist.user)
    uploaded = SimpleUploadedFile(
        'skierowanie.pdf',
        b'%PDF-1.4 test document',
        content_type='application/pdf',
    )
    response = api_client.post(
        '/api/v1/therapist/documents/',
        {'patient_id': str(patient.id), 'title': 'Skierowanie', 'file': uploaded},
        format='multipart',
    )
    assert response.status_code == status.HTTP_201_CREATED
    events = _drain(patient_q, expected=1)
    assert events[0].type == 'document.created'
    assert events[0].resource_id == response.data['id']


@pytest.mark.django_db
def test_clinical_recommendation_publishes_document_sse(
    api_client,
    therapist,
    patient,
):
    from treatment.models import TreatmentEpisode

    therapist.qualification_level = 'MAGISTER'
    therapist.experience_years = 5
    therapist.save()
    episode = TreatmentEpisode.objects.create(patient=patient, icd10_code='M25.5')
    patient_q = get_sse_bus().subscribe(str(patient.user_id))
    api_client.force_authenticate(user=therapist.user)

    response = api_client.post(
        f'/api/v1/episodes/{episode.id}/diagnostic-recommendations/',
        {
            'recommendation_type': 'SPECIALIST_CONSULTATION',
            'target_specialty': 'Ortopeda',
            'body_area': 'Kolano L',
            'justification': 'Ból po urazie.',
            'red_flags_noted': False,
            'funding_hint': 'NFZ_VIA_DOCTOR',
        },
        format='json',
    )
    assert response.status_code == status.HTTP_201_CREATED
    events = _drain(patient_q, expected=1)
    assert events[0].type == 'document.created'
    assert events[0].resource_id == response.data['id']
