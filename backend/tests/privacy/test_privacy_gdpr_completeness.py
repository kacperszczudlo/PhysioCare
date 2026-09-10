import json
import pytest

from documents.models import MedicalDocument
from privacy.account_deletion import anonymize_user_for_deletion
from privacy.export import build_patient_export
from treatment.models import TreatmentEpisode


@pytest.mark.django_db
def test_build_patient_export_contains_all_sections_and_no_secrets(
    patient, therapist, therapy_type
):
    # Arrange
    doc = MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='USG Kolana',
        file_url='/media/documents/usg.pdf',
        mime_type='application/pdf',
    )
    episode = TreatmentEpisode.objects.create(
        patient=patient,
        icd10_code='M17.1',
        summary_note='Choroba zwyrodnieniowa kolana',
    )

    # Act
    export_data = build_patient_export(patient.user, patient)
    from django.core.serializers.json import DjangoJSONEncoder
    raw_json = json.dumps(export_data, cls=DjangoJSONEncoder)

    # Assert - Structure
    assert 'exported_at' in export_data
    assert export_data['profile']['email'] == patient.user.email
    assert len(export_data['documents']) == 1
    assert export_data['documents'][0]['title'] == 'USG Kolana'
    assert len(export_data['episodes']) == 1
    assert export_data['episodes'][0]['icd10_code'] == 'M17.1'

    # Assert - Security (No raw passwords or JWT secret tokens in payload)
    assert 'password' not in export_data['profile']
    assert 'secret' not in raw_json.lower()
    assert 'jwt' not in raw_json.lower()


@pytest.mark.django_db
def test_anonymize_user_for_deletion_anonymizes_personal_data(patient):
    # Arrange
    user = patient.user
    original_email = user.email

    # Act
    anonymize_user_for_deletion(user, source='user_request')
    user.refresh_from_db()
    patient.refresh_from_db()

    # Assert
    assert user.is_active is False
    assert user.email != original_email
    assert user.email.endswith('@deleted.invalid')
    assert user.first_name == 'Usunięte'
    assert user.last_name == 'Konto'
