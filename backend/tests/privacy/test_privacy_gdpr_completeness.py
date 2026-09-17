import json
from typing import TYPE_CHECKING

import pytest

from documents.models import MedicalDocument
from privacy.account_deletion import anonymize_user_for_deletion
from privacy.export import build_patient_export
from treatment.models import TreatmentEpisode

if TYPE_CHECKING:
    from patients.models import PatientProfile
    from scheduling.models import TherapyType
    from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_build_patient_export_contains_all_sections_and_no_secrets(
    patient: 'PatientProfile',
    therapist: 'TherapistProfile',
    therapy_type: 'TherapyType',
) -> None:
    """Sprawdza, że eksport danych RODO zawiera wszystkie wymagane sekcje i nie zawiera sekretów ani haseł."""
    # Arrange
    MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='USG Kolana',
        file_url='/media/documents/usg.pdf',
        mime_type='application/pdf',
    )
    TreatmentEpisode.objects.create(
        patient=patient,
        icd10_code='M17.1',
        summary_note='Choroba zwyrodnieniowa kolana',
    )

    export_data = build_patient_export(patient.user, patient)
    from django.core.serializers.json import DjangoJSONEncoder
    raw_json: str = json.dumps(export_data, cls=DjangoJSONEncoder)

    # Assert
    assert 'exported_at' in export_data
    assert export_data['profile']['email'] == patient.user.email
    assert len(export_data['documents']) == 1
    assert export_data['documents'][0]['title'] == 'USG Kolana'
    assert len(export_data['episodes']) == 1
    assert export_data['episodes'][0]['icd10_code'] == 'M17.1'

    assert 'password' not in export_data['profile']
    assert 'secret' not in raw_json.lower()
    assert 'jwt' not in raw_json.lower()


@pytest.mark.django_db
def test_anonymize_user_for_deletion_anonymizes_personal_data(patient: 'PatientProfile') -> None:
    """Sprawdza bezpowrotną anonimizację danych identyfikacyjnych pacjenta podczas usuwania konta."""
    # Arrange
    user = patient.user
    original_email: str = user.email

    anonymize_user_for_deletion(user, source='user_request')
    user.refresh_from_db()
    patient.refresh_from_db()

    # Assert
    assert user.is_active is False
    assert user.email != original_email
    assert user.email.endswith('@deleted.invalid')
    assert user.first_name == 'Usunięte'
    assert user.last_name == 'Konto'

