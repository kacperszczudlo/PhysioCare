from typing import TYPE_CHECKING

import pytest
from rest_framework import status

from treatment.models import BodyAreaPain, TreatmentEpisode

if TYPE_CHECKING:
    from rest_framework.test import APIClient
    from patients.models import PatientProfile
    from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_body_pain_create_with_treatment_targets(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
    patient: 'PatientProfile',
) -> None:
    """Sprawdza pomyślne dodanie wpisu bólowego z celami terapeutycznymi do epizodu."""
    # Arrange
    episode = TreatmentEpisode.objects.create(
        patient=patient,
        icd10_code='M54.5',
        summary_note='Ból lędźwiowy',
    )
    api_client.force_authenticate(user=therapist.user)

    # Act
    response = api_client.post(
        f'/api/v1/episodes/{episode.id}/body-pain/',
        {
            'body_region': 'left-lower-back',
            'view_side': 'BACK',
            'vas_score': 7,
            'pain_character': ['SHARP', 'RADIATING'],
            'treatment_targets': ['L_SPINE', 'QL_L'],
        },
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['body_region'] == 'left-lower-back'
    assert response.data['treatment_targets'] == ['L_SPINE', 'QL_L']
    entry = BodyAreaPain.objects.get(id=response.data['id'])
    assert entry.treatment_targets == ['L_SPINE', 'QL_L']


@pytest.mark.django_db
def test_body_pain_update_treatment_targets(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
    patient: 'PatientProfile',
) -> None:
    """Sprawdza aktualizację skali bólu VAS i celów terapeutycznych w istniejącym wpisie."""
    # Arrange
    episode = TreatmentEpisode.objects.create(patient=patient, icd10_code='M25.5')
    entry = BodyAreaPain.objects.create(
        episode=episode,
        body_region='right-quadriceps',
        view_side='FRONT',
        vas_score=6,
        pain_character=['DULL'],
        treatment_targets=['QUAD_R'],
    )
    api_client.force_authenticate(user=therapist.user)

    # Act
    response = api_client.patch(
        f'/api/v1/episodes/{episode.id}/body-pain/{entry.id}/',
        {
            'vas_score': 3,
            'treatment_targets': ['QUAD_R', 'HIP_JT_R'],
        },
        format='json',
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.data['vas_score'] == 3
    assert response.data['treatment_targets'] == ['QUAD_R', 'HIP_JT_R']
    entry.refresh_from_db()
    assert entry.treatment_targets == ['QUAD_R', 'HIP_JT_R']


@pytest.mark.django_db
def test_body_pain_delete(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
    patient: 'PatientProfile',
) -> None:
    """Sprawdza usunięcie wpisu obszaru bólowego z epizodu leczenia."""
    # Arrange
    episode = TreatmentEpisode.objects.create(patient=patient, icd10_code='M54.5')
    entry = BodyAreaPain.objects.create(
        episode=episode,
        body_region='left-lower-back',
        view_side='BACK',
        vas_score=8,
        pain_character=['SHARP'],
        treatment_targets=['QL_L'],
    )
    api_client.force_authenticate(user=therapist.user)

    # Act
    response = api_client.delete(
        f'/api/v1/episodes/{episode.id}/body-pain/{entry.id}/',
    )

    # Assert
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not BodyAreaPain.objects.filter(id=entry.id).exists()

