from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.urls import reverse
import pytest
from rest_framework import status

from documents.models import MedicalDocument


@pytest.mark.django_db
def test_download_document_success(api_client, patient, therapist, tmp_path):
    # Arrange
    media_doc_dir = Path(settings.MEDIA_ROOT) / 'documents'
    media_doc_dir.mkdir(parents=True, exist_ok=True)
    file_path = media_doc_dir / 'test_download.pdf'
    file_path.write_bytes(b'%PDF-1.4 test file content')

    doc = MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Dokument Pobierany',
        file_url='/media/documents/test_download.pdf',
        mime_type='application/pdf',
    )

    api_client.force_authenticate(user=patient.user)
    url = reverse('document-download', kwargs={'pk': doc.id})

    try:
        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        assert response.headers['Cache-Control'] == 'private, no-store'
        assert response.getvalue() == b'%PDF-1.4 test file content'
    finally:
        if file_path.exists():
            file_path.unlink()


@pytest.mark.django_db
def test_therapist_downloads_patient_document_success(api_client, patient, therapist, tmp_path):
    # Arrange
    media_doc_dir = Path(settings.MEDIA_ROOT) / 'documents'
    media_doc_dir.mkdir(parents=True, exist_ok=True)
    file_path = media_doc_dir / 'test_therapist_dl.pdf'
    file_path.write_bytes(b'%PDF-1.4 therapist access')

    doc = MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Dokument Terapeuty',
        file_url='/media/documents/test_therapist_dl.pdf',
        mime_type='application/pdf',
    )

    api_client.force_authenticate(user=therapist.user)
    url = reverse('document-download', kwargs={'pk': doc.id})

    try:
        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.getvalue() == b'%PDF-1.4 therapist access'
    finally:
        if file_path.exists():
            file_path.unlink()


@pytest.mark.django_db
def test_other_therapist_cannot_download_document(api_client, patient, therapist, therapist_b):
    # Arrange
    doc = MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Tajny Dokument',
        file_url='/media/documents/secret.pdf',
        mime_type='application/pdf',
    )

    api_client.force_authenticate(user=therapist_b.user)
    url = reverse('document-download', kwargs={'pk': doc.id})

    # Act
    response = api_client.get(url)

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_nonexistent_document_returns_404(api_client, patient):
    # Arrange
    api_client.force_authenticate(user=patient.user)
    import uuid
    url = reverse('document-download', kwargs={'pk': uuid.uuid4()})

    # Act
    response = api_client.get(url)

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_download_prevents_directory_traversal(api_client, patient, therapist):
    # Arrange
    doc = MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Traversal Attempt',
        file_url='/media/../settings.py',
        mime_type='application/pdf',
    )

    api_client.force_authenticate(user=patient.user)
    url = reverse('document-download', kwargs={'pk': doc.id})

    # Act
    response = api_client.get(url)

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_download_missing_file_on_disk_returns_404(api_client, patient, therapist):
    # Arrange
    doc = MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Missing Disk File',
        file_url='/media/documents/non_existent_file_xyz.pdf',
        mime_type='application/pdf',
    )

    api_client.force_authenticate(user=patient.user)
    url = reverse('document-download', kwargs={'pk': doc.id})

    # Act
    response = api_client.get(url)

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
