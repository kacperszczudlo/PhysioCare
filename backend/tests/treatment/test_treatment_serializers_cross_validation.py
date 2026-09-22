from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from django.utils import timezone

from scheduling.models import Visit, VisitStatus
from treatment.models import (
    DiagnosticRecommendation,
    EpisodeStatus,
    RecommendationType,
    TreatmentEpisode,
)
from treatment.patient_documents import build_clinical_documents_for_patient
from treatment.serializers import VisitNoteSerializer

if TYPE_CHECKING:
    from patients.models import PatientProfile
    from scheduling.models import TherapyType
    from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_visit_note_serializer_rejects_visit_from_different_patient(
    therapist: 'TherapistProfile',
    patient: 'PatientProfile',
    patient_profiles: list['PatientProfile'],
    therapy_type: 'TherapyType',
) -> None:
    """Sprawdza odrzucenie powiązania notatki medycznej z wizytą należącą do innego pacjenta niż epizod leczenia."""
    # Arrange
    patient_b = patient_profiles[1]
    episode_patient_a = TreatmentEpisode.objects.create(
        patient=patient,
        therapist=therapist,
        icd10_code='M23.2',
        status=EpisodeStatus.IN_PROGRESS,
    )

    start_at = timezone.now() + timedelta(days=1)
    end_at = start_at + timedelta(hours=1)
    visit_patient_b = Visit.objects.create(
        therapist=therapist,
        patient=patient_b,
        therapy_type=therapy_type,
        start_at=start_at,
        end_at=end_at,
        status=VisitStatus.COMPLETED,
        location_address='Gabinet 1',
    )

    serializer = VisitNoteSerializer(
        data={'content': 'Notatka medyczna z przebiegu zabiegu.', 'visit': str(visit_patient_b.id)},
        context={'episode': episode_patient_a},
    )

    # Act & Assert
    assert serializer.is_valid() is False
    assert 'visit' in serializer.errors
    assert any('Wizyta nie należy do pacjenta tego epizodu.' in str(err) for err in serializer.errors['visit'])


@pytest.mark.django_db
def test_visit_note_serializer_rejects_visit_from_different_episode(
    therapist: 'TherapistProfile',
    patient: 'PatientProfile',
    therapy_type: 'TherapyType',
) -> None:
    """Sprawdza odrzucenie przypisania notatki do wizyty, która jest powiązana z innym epizodem leczenia tego samego pacjenta."""
    # Arrange
    episode_1 = TreatmentEpisode.objects.create(
        patient=patient,
        therapist=therapist,
        icd10_code='M23.2',
        status=EpisodeStatus.IN_PROGRESS,
    )
    episode_2 = TreatmentEpisode.objects.create(
        patient=patient,
        therapist=therapist,
        icd10_code='S83.5',
        status=EpisodeStatus.IN_PROGRESS,
    )

    start_at = timezone.now() + timedelta(days=2)
    end_at = start_at + timedelta(hours=1)
    visit_ep_1 = Visit.objects.create(
        therapist=therapist,
        patient=patient,
        episode=episode_1,
        therapy_type=therapy_type,
        start_at=start_at,
        end_at=end_at,
        status=VisitStatus.COMPLETED,
        location_address='Gabinet 1',
    )

    serializer = VisitNoteSerializer(
        data={'content': 'Błędne podpięcie pod drugi epizod.', 'visit': str(visit_ep_1.id)},
        context={'episode': episode_2},
    )

    # Act & Assert
    assert serializer.is_valid() is False
    assert 'visit' in serializer.errors
    assert any('Wizyta nie należy do tego epizodu.' in str(err) for err in serializer.errors['visit'])


@pytest.mark.django_db
def test_build_clinical_documents_type_validation() -> None:
    """Weryfikuje zgłaszanie wyjątku TypeError w funkcji build_clinical_documents_for_patient przy nieprawidłowych typach parametrów."""
    # Act & Assert
    with pytest.raises(TypeError, match='Parametr patient nie może być None.'):
        build_clinical_documents_for_patient(None)

    with pytest.raises(TypeError, match='Parametr kind musi być ciągiem znaków lub None.'):
        build_clinical_documents_for_patient(patient=object(), kind=12345)  # type: ignore[arg-type]


@pytest.mark.django_db
def test_build_clinical_documents_returns_structured_records(
    therapist: 'TherapistProfile',
    patient: 'PatientProfile',
) -> None:
    """Sprawdza budowanie chronologicznej struktury dokumentów medycznych widocznych dla pacjenta."""
    # Arrange
    episode = TreatmentEpisode.objects.create(
        patient=patient,
        therapist=therapist,
        icd10_code='M54.5',
        summary_note='Podsumowanie epizodu bólowego L4-L5',
        status=EpisodeStatus.IN_PROGRESS,
    )
    rec = DiagnosticRecommendation.objects.create(
        episode=episode,
        therapist=therapist,
        recommendation_type=RecommendationType.SPECIALIST_CONSULTATION,
        target_specialty='Ortopedia',
        body_area='Staw kolanowy',
        justification='Podejrzenie uszkodzenia łąkotki bocznej po urazie.',
    )

    # Act
    docs = build_clinical_documents_for_patient(patient)

    # Assert
    assert isinstance(docs, list)
    assert len(docs) >= 1
    rec_doc = next((d for d in docs if d.get('id') == str(rec.id)), None)
    assert rec_doc is not None
    assert rec_doc['kind'] == 'recommendation'
