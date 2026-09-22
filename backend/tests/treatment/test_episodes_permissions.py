from typing import TYPE_CHECKING

import pytest
from rest_framework import status

from patients.models import PatientTherapistLink
from treatment.models import (
    TreatmentEpisode,
)

if TYPE_CHECKING:
    from rest_framework.test import APIClient

    from patients.models import PatientProfile
    from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_other_therapist_cannot_update_other_therapist_episode(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
    therapist_b: 'TherapistProfile',
    patient: 'PatientProfile',
) -> None:
    """Sprawdza, że połączony fizjoterapeuta B widzi epizod terapeuty A jako tylko do odczytu i nie może go edytować."""
    # Arrange
    PatientTherapistLink.objects.create(patient=patient, therapist=therapist_b, status='ACTIVE')

    api_client.force_authenticate(user=therapist.user)
    # Act
    create_resp = api_client.post(
        f'/api/v1/patients/{patient.id}/episodes/',
        {'icd10_code': 'M54.5', 'summary_note': 'Epizod od A'},
        format='json',
    )
    # Assert
    assert create_resp.status_code == status.HTTP_201_CREATED
    episode_id = create_resp.data['id']
    assert create_resp.data['is_read_only'] is False

    api_client.force_authenticate(user=therapist_b.user)
    get_resp = api_client.get(f'/api/v1/episodes/{episode_id}/')
    assert get_resp.status_code == status.HTTP_200_OK
    assert get_resp.data['is_read_only'] is True

    patch_resp = api_client.patch(
        f'/api/v1/episodes/{episode_id}/',
        {'summary_note': 'Niedozwolona zmiana B'},
        format='json',
    )
    assert patch_resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_therapist_notes_privacy_isolation(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
    therapist_b: 'TherapistProfile',
    patient: 'PatientProfile',
) -> None:
    """Sprawdza pełną prywatność i izolację notatek klinicznych poszczególnych fizjoterapeutów."""
    # Arrange
    PatientTherapistLink.objects.create(patient=patient, therapist=therapist_b, status='ACTIVE')

    episode = TreatmentEpisode.objects.create(patient=patient, therapist=therapist, icd10_code='M54.5')

    api_client.force_authenticate(user=therapist.user)
    # Act
    api_client.post(
        f'/api/v1/episodes/{episode.id}/notes/',
        {'content': 'Notatka poufna A'},
        format='json',
    )

    api_client.force_authenticate(user=therapist_b.user)
    list_b = api_client.get(f'/api/v1/episodes/{episode.id}/notes/')
    # Assert
    assert list_b.status_code == status.HTTP_200_OK
    assert list_b.data['count'] == 0

    api_client.post(
        f'/api/v1/episodes/{episode.id}/notes/',
        {'content': 'Notatka B'},
        format='json',
    )

    api_client.force_authenticate(user=therapist.user)
    list_a = api_client.get(f'/api/v1/episodes/{episode.id}/notes/')
    assert list_a.status_code == status.HTTP_200_OK
    assert list_a.data['count'] == 1
    assert list_a.data['results'][0]['content'] == 'Notatka poufna A'


@pytest.mark.django_db
def test_other_therapist_cannot_modify_or_delete_clinical_history_items(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
    therapist_b: 'TherapistProfile',
    patient: 'PatientProfile',
) -> None:
    """Sprawdza blokadę edycji i usuwania elementów historii klinicznej utworzonych przez innego fizjoterapeutę."""
    # Arrange
    PatientTherapistLink.objects.create(patient=patient, therapist=therapist_b, status='ACTIVE')
    episode = TreatmentEpisode.objects.create(patient=patient, therapist=therapist, icd10_code='M54.5')

    api_client.force_authenticate(user=therapist.user)
    # Act
    rec_resp = api_client.post(
        f'/api/v1/episodes/{episode.id}/diagnostic-recommendations/',
        {
            'recommendation_type': 'SPECIALIST_CONSULTATION',
            'justification': 'Konieczna konsultacja ortopedyczna',
        },
        format='json',
    )
    # Assert
    assert rec_resp.status_code == status.HTTP_201_CREATED
    rec_id = rec_resp.data['id']
    assert rec_resp.data['is_read_only'] is False

    api_client.force_authenticate(user=therapist_b.user)
    rec_list = api_client.get(f'/api/v1/episodes/{episode.id}/diagnostic-recommendations/')
    assert rec_list.status_code == status.HTTP_200_OK
    item_b = [r for r in rec_list.data['results'] if r['id'] == rec_id][0]
    assert item_b['is_read_only'] is True

    patch_resp = api_client.patch(
        f'/api/v1/episodes/{episode.id}/diagnostic-recommendations/{rec_id}/',
        {'justification': 'Zmiana przez B'},
        format='json',
    )
    assert patch_resp.status_code == status.HTTP_403_FORBIDDEN

    del_resp = api_client.delete(f'/api/v1/episodes/{episode.id}/diagnostic-recommendations/{rec_id}/')
    assert del_resp.status_code == status.HTTP_403_FORBIDDEN


