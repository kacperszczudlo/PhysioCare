from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status

from documents.models import MedicalDocument
from scheduling.models import Visit
from treatment.models import TreatmentEpisode


@pytest.mark.django_db
@patch('documents.views.save_upload', return_value=('/media/documents/test.pdf', 'application/pdf'))
@patch('documents.views.notify_new_document')
def test_therapist_uploads_document_successfully(
    mock_notify: object, mock_save: object, api_client: object, therapist: object, patient: object,
) -> None:
    """Sprawdza pomyślne przesłanie nowego dokumentu medycznego pacjenta przez fizjoterapeutę."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)
    uploaded_file: SimpleUploadedFile = SimpleUploadedFile(
        'test.pdf', b'%PDF-1.4 test pdf content', content_type='application/pdf'
    )

    response: object = api_client.post(
        '/api/v1/therapist/documents/',
        {
            'file': uploaded_file,
            'patient_id': patient.id,
            'title': 'Badanie Rezonansu Magnetycznego',
        },
        format='multipart',
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['title'] == 'Badanie Rezonansu Magnetycznego'
    assert MedicalDocument.objects.filter(patient=patient).count() == 1
    mock_save.assert_called_once()
    mock_notify.assert_called_once()


@pytest.mark.django_db
def test_upload_without_file_returns_400(
    api_client: object, therapist: object, patient: object,
) -> None:
    """Sprawdza zwrócenie błędu 400 FILE_REQUIRED przy próbie wysłania dokumentu bez pliku."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)

    response: object = api_client.post(
        '/api/v1/therapist/documents/',
        {
            'patient_id': patient.id,
            'title': 'Dokument bez pliku',
        },
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error']['code'] == 'FILE_REQUIRED'


@pytest.mark.django_db
def test_therapist_cannot_upload_for_other_therapist_patient(
    api_client: object, therapist_b: object, patient: object,
) -> None:
    """Sprawdza odrzucenie próby dodania dokumentu dla pacjenta innego fizjoterapeuty (BOLA)."""
    # Arrange
    api_client.force_authenticate(user=therapist_b.user)
    uploaded_file: SimpleUploadedFile = SimpleUploadedFile(
        'test.pdf', b'%PDF-1.4 test pdf content', content_type='application/pdf'
    )

    response: object = api_client.post(
        '/api/v1/therapist/documents/',
        {
            'file': uploaded_file,
            'patient_id': patient.id,
            'title': 'Obcy pacjent',
        },
        format='multipart',
    )

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_upload_with_invalid_blank_title_returns_400(
    api_client: object, therapist: object, patient: object,
) -> None:
    """Sprawdza odrzucenie pustego lub składającego się z samych spacji tytułu dokumentu."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)
    uploaded_file: SimpleUploadedFile = SimpleUploadedFile(
        'test.pdf', b'%PDF-1.4 test pdf content', content_type='application/pdf'
    )

    response: object = api_client.post(
        '/api/v1/therapist/documents/',
        {
            'file': uploaded_file,
            'patient_id': patient.id,
            'title': '   ',
        },
        format='multipart',
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error']['code'] == 'VALIDATION'


@pytest.mark.django_db
def test_upload_with_title_too_long_returns_400(
    api_client: object, therapist: object, patient: object,
) -> None:
    """Sprawdza odrzucenie tytułu dokumentu przekraczającego dopuszczalną długość 200 znaków."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)
    uploaded_file: SimpleUploadedFile = SimpleUploadedFile(
        'test.pdf', b'%PDF-1.4 test pdf content', content_type='application/pdf'
    )

    response: object = api_client.post(
        '/api/v1/therapist/documents/',
        {
            'file': uploaded_file,
            'patient_id': patient.id,
            'title': 'A' * 201,
        },
        format='multipart',
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error']['code'] == 'VALIDATION'


@pytest.mark.django_db
def test_upload_with_invalid_visit_id_returns_400(
    api_client: object, therapist: object, patient: object,
) -> None:
    """Sprawdza odrzucenie nieistniejącego identyfikatora wizyty przy powiązywaniu dokumentu."""
    # Arrange
    import uuid
    api_client.force_authenticate(user=therapist.user)
    uploaded_file: SimpleUploadedFile = SimpleUploadedFile(
        'test.pdf', b'%PDF-1.4 test pdf content', content_type='application/pdf'
    )

    response: object = api_client.post(
        '/api/v1/therapist/documents/',
        {
            'file': uploaded_file,
            'patient_id': patient.id,
            'visit_id': str(uuid.uuid4()),
        },
        format='multipart',
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error']['code'] == 'VALIDATION'
    assert 'visit_id' in response.data['error']['details']


@pytest.mark.django_db
def test_upload_with_invalid_episode_id_returns_400(
    api_client: object, therapist: object, patient: object,
) -> None:
    """Sprawdza odrzucenie nieistniejącego identyfikatora epizodu leczenia przy powiązywaniu dokumentu."""
    # Arrange
    import uuid
    api_client.force_authenticate(user=therapist.user)
    uploaded_file: SimpleUploadedFile = SimpleUploadedFile(
        'test.pdf', b'%PDF-1.4 test pdf content', content_type='application/pdf'
    )

    response: object = api_client.post(
        '/api/v1/therapist/documents/',
        {
            'file': uploaded_file,
            'patient_id': patient.id,
            'episode_id': str(uuid.uuid4()),
        },
        format='multipart',
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error']['code'] == 'VALIDATION'
    assert 'episode_id' in response.data['error']['details']


@pytest.mark.django_db
@patch('documents.views.save_upload', return_value=('/media/documents/test.pdf', 'application/pdf'))
@patch('documents.views.notify_new_document')
def test_upload_linked_to_valid_visit_and_episode(
    mock_notify: object, mock_save: object, api_client: object, therapist: object, patient: object, therapy_type: object,
) -> None:
    """Sprawdza pomyślne powiązanie dokumentu z poprawną wizytą oraz epizodem leczenia."""
    # Arrange
    episode: TreatmentEpisode = TreatmentEpisode.objects.create(
        patient=patient,
        icd10_code='M54.5',
        summary_note='Ból kręgosłupa',
    )
    visit: Visit = Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at='2026-10-01T10:00:00Z',
        end_at='2026-10-01T10:45:00Z',
        status='SCHEDULED',
    )

    api_client.force_authenticate(user=therapist.user)
    uploaded_file: SimpleUploadedFile = SimpleUploadedFile(
        'test.pdf', b'PDF-content', content_type='application/pdf'
    )

    response: object = api_client.post(
        '/api/v1/therapist/documents/',
        {
            'file': uploaded_file,
            'patient_id': patient.id,
            'visit_id': visit.id,
            'episode_id': episode.id,
            'title': 'Karta wizyty',
        },
        format='multipart',
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    doc: MedicalDocument = MedicalDocument.objects.get(pk=response.data['id'])
    assert doc.visit == visit
    assert doc.episode == episode

