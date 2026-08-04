import pytest
from rest_framework import status

from treatment.models import TreatmentEpisode


@pytest.mark.django_db
def test_therapist_creates_and_lists_patient_episodes(api_client, therapist, patient):
    api_client.force_authenticate(user=therapist.user)

    create_response = api_client.post(
        f'/api/v1/patients/{patient.id}/episodes/',
        {
            'icd10_code': 'M54.5',
            'summary_note': 'Ból lędźwiowy',
        },
        format='json',
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    assert create_response.data['icd10_code'] == 'M54.5'
    assert create_response.data['status'] == 'IN_PROGRESS'
    assert TreatmentEpisode.objects.filter(patient=patient).count() == 1

    list_response = api_client.get(f'/api/v1/patients/{patient.id}/episodes/')
    assert list_response.status_code == status.HTTP_200_OK
    assert list_response.data['count'] == 1
    assert list_response.data['results'][0]['id'] == create_response.data['id']


@pytest.mark.django_db
def test_therapist_cannot_access_other_therapist_episode(
    api_client, therapist, therapist_b, patient,
):
    episode = TreatmentEpisode.objects.create(
        patient=patient,
        icd10_code='M25.5',
        summary_note='Cudzy epizod',
    )

    api_client.force_authenticate(user=therapist_b.user)
    response = api_client.get(f'/api/v1/episodes/{episode.id}/')

    assert response.status_code == status.HTTP_404_NOT_FOUND
