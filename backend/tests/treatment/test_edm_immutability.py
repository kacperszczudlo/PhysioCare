import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status

from core.field_policies import normalize_and_validate_icd10
from treatment.models import EpisodeStatus, TreatmentEpisode
from treatment.serializers import TreatmentEpisodeSerializer


from typing import TYPE_CHECKING

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status

from core.field_policies import normalize_and_validate_icd10
from treatment.models import EpisodeStatus, TreatmentEpisode
from treatment.serializers import TreatmentEpisodeSerializer

if TYPE_CHECKING:
    from rest_framework.test import APIClient
    from patients.models import PatientProfile
    from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_icd10_format_validation_accepts_valid_codes() -> None:
    """Weryfikacja poprawnych formatów kodów rozpoznań ICD-10 (np. M23.2, S83.5)."""
    # Assert
    assert normalize_and_validate_icd10('M23.2') == 'M23.2'
    assert normalize_and_validate_icd10('s83.5') == 'S83.5'
    assert normalize_and_validate_icd10('  M54.5  ') == 'M54.5'


def test_icd10_format_validation_rejects_invalid_codes() -> None:
    """Weryfikacja odrzucania niepoprawnych kodów rozpoznań ICD-10."""
    # Act
    with pytest.raises(DjangoValidationError):
        normalize_and_validate_icd10('INVALID_CODE')

    with pytest.raises(DjangoValidationError):
        normalize_and_validate_icd10('123456')


@pytest.mark.django_db
def test_treatment_episode_serializer_icd10_validation() -> None:
    """Serializer epizodu leczenia zgłasza błąd walidacji dla niepoprawnego kodu ICD-10."""
    # Arrange
    serializer = TreatmentEpisodeSerializer(data={
        'title': 'Epizod testowy',
        'icd10_code': 'BŁĘDNY_KOD_ICD10',
        'status': EpisodeStatus.IN_PROGRESS,
    })

    # Assert
    assert serializer.is_valid() is False
    assert 'icd10_code' in serializer.errors


@pytest.mark.django_db
def test_other_therapist_cannot_modify_closed_episode(
    api_client: 'APIClient',
    therapist: 'TherapistProfile',
    therapist_b: 'TherapistProfile',
    patient: 'PatientProfile',
) -> None:
    """Inny terapeuta (BOLA / AuthZ) nie może modyfikować epizodu leczenia utworzonego przez innego terapeutę."""
    # Arrange
    episode = TreatmentEpisode.objects.create(
        patient=patient,
        therapist=therapist,
        icd10_code='M23.2',
        summary_note='Pierwotne uzgodnienia kliniczne',
        status=EpisodeStatus.COMPLETED_SUCCESS,
    )

    api_client.force_authenticate(user=therapist_b.user)
    # Act
    response = api_client.patch(
        f'/api/v1/patients/{patient.id}/episodes/{episode.id}/',
        data={'summary_note': 'Próba nieuprawnionej nadpisania dokumentacji'},
        format='json',
    )

    # Assert
    assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

