import pytest
from rest_framework import status

from patients.models import PatientTherapistLink
from treatment.models import (
    DiagnosticRecommendation,
    MedicalDeviceOrder,
    PhysicianOrderRefusal,
    ReceptaNaRuchReferral,
    TreatmentEpisode,
    VisitNote,
)


@pytest.mark.django_db
def test_other_therapist_cannot_update_other_therapist_episode(api_client, therapist, therapist_b, patient):
    # Both therapists linked to the patient
    PatientTherapistLink.objects.create(patient=patient, therapist=therapist_b, status='ACTIVE')

    # Therapist A creates episode
    api_client.force_authenticate(user=therapist.user)
    create_resp = api_client.post(
        f'/api/v1/patients/{patient.id}/episodes/',
        {'icd10_code': 'M54.5', 'summary_note': 'Epizod od A'},
        format='json',
    )
    assert create_resp.status_code == status.HTTP_201_CREATED
    episode_id = create_resp.data['id']
    assert create_resp.data['is_read_only'] is False

    # Therapist B retrieves episode -> sees is_read_only=True
    api_client.force_authenticate(user=therapist_b.user)
    get_resp = api_client.get(f'/api/v1/episodes/{episode_id}/')
    assert get_resp.status_code == status.HTTP_200_OK
    assert get_resp.data['is_read_only'] is True

    # Therapist B tries to patch episode -> 403 Forbidden
    patch_resp = api_client.patch(
        f'/api/v1/episodes/{episode_id}/',
        {'summary_note': 'Niedozwolona zmiana B'},
        format='json',
    )
    assert patch_resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_therapist_notes_privacy_isolation(api_client, therapist, therapist_b, patient):
    PatientTherapistLink.objects.create(patient=patient, therapist=therapist_b, status='ACTIVE')

    episode = TreatmentEpisode.objects.create(patient=patient, therapist=therapist, icd10_code='M54.5')

    # Therapist A adds note
    api_client.force_authenticate(user=therapist.user)
    api_client.post(
        f'/api/v1/episodes/{episode.id}/notes/',
        {'content': 'Notatka poufna A'},
        format='json',
    )

    # Therapist B lists notes for same episode -> empty list
    api_client.force_authenticate(user=therapist_b.user)
    list_b = api_client.get(f'/api/v1/episodes/{episode.id}/notes/')
    assert list_b.status_code == status.HTTP_200_OK
    assert list_b.data['count'] == 0

    # Therapist B adds note
    api_client.post(
        f'/api/v1/episodes/{episode.id}/notes/',
        {'content': 'Notatka B'},
        format='json',
    )

    # Therapist A lists notes -> sees only 1 note (A's note)
    api_client.force_authenticate(user=therapist.user)
    list_a = api_client.get(f'/api/v1/episodes/{episode.id}/notes/')
    assert list_a.status_code == status.HTTP_200_OK
    assert list_a.data['count'] == 1
    assert list_a.data['results'][0]['content'] == 'Notatka poufna A'


@pytest.mark.django_db
def test_other_therapist_cannot_modify_or_delete_clinical_history_items(
    api_client, therapist, therapist_b, patient,
):
    PatientTherapistLink.objects.create(patient=patient, therapist=therapist_b, status='ACTIVE')
    episode = TreatmentEpisode.objects.create(patient=patient, therapist=therapist, icd10_code='M54.5')

    # Therapist A creates recommendation
    api_client.force_authenticate(user=therapist.user)
    rec_resp = api_client.post(
        f'/api/v1/episodes/{episode.id}/diagnostic-recommendations/',
        {
            'recommendation_type': 'SPECIALIST_CONSULTATION',
            'justification': 'Konieczna konsultacja ortopedyczna',
        },
        format='json',
    )
    assert rec_resp.status_code == status.HTTP_201_CREATED
    rec_id = rec_resp.data['id']
    assert rec_resp.data['is_read_only'] is False

    # Therapist B views recommendation -> is_read_only is True
    api_client.force_authenticate(user=therapist_b.user)
    rec_list = api_client.get(f'/api/v1/episodes/{episode.id}/diagnostic-recommendations/')
    assert rec_list.status_code == status.HTTP_200_OK
    item_b = [r for r in rec_list.data['results'] if r['id'] == rec_id][0]
    assert item_b['is_read_only'] is True

    # Therapist B attempts update/delete -> 403 Forbidden
    patch_resp = api_client.patch(
        f'/api/v1/episodes/{episode.id}/diagnostic-recommendations/{rec_id}/',
        {'justification': 'Zmiana przez B'},
        format='json',
    )
    assert patch_resp.status_code == status.HTTP_403_FORBIDDEN

    del_resp = api_client.delete(f'/api/v1/episodes/{episode.id}/diagnostic-recommendations/{rec_id}/')
    assert del_resp.status_code == status.HTTP_403_FORBIDDEN
