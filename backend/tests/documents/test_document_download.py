from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status

from documents.models import MedicalDocument


@pytest.mark.django_db
def test_download_document_success(
    api_client: object, patient: object, therapist: object, tmp_path: object,
) -> None:
    """Sprawdza pomyślne pobranie pliku dokumentu medycznego przez pacjenta."""
    # Arrange
    media_doc_dir: Path = Path(settings.MEDIA_ROOT) / 'documents'
    media_doc_dir.mkdir(parents=True, exist_ok=True)
    file_path: Path = media_doc_dir / 'test_download.pdf'
    file_path.write_bytes(b'%PDF-1.4 test file content')

    doc: MedicalDocument = MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Dokument Pobierany',
        file_url='/media/documents/test_download.pdf',
        mime_type='application/pdf',
    )

    api_client.force_authenticate(user=patient.user)
    url: str = reverse('document-download', kwargs={'pk': doc.id})

    try:
        response: object = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        assert response.headers['Cache-Control'] == 'private, no-store'
        assert response.headers['Content-Security-Policy'] == "sandbox; default-src 'none'"
        assert response.getvalue() == b'%PDF-1.4 test file content'
    finally:
        if file_path.exists():
            file_path.unlink()


@pytest.mark.django_db
def test_therapist_downloads_patient_document_success(
    api_client: object, patient: object, therapist: object, tmp_path: object,
) -> None:
    """Sprawdza pomyślne pobranie pliku dokumentu pacjenta przez przypisanego fizjoterapeutę."""
    # Arrange
    media_doc_dir: Path = Path(settings.MEDIA_ROOT) / 'documents'
    media_doc_dir.mkdir(parents=True, exist_ok=True)
    file_path: Path = media_doc_dir / 'test_therapist_dl.pdf'
    file_path.write_bytes(b'%PDF-1.4 therapist access')

    doc: MedicalDocument = MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Dokument Terapeuty',
        file_url='/media/documents/test_therapist_dl.pdf',
        mime_type='application/pdf',
    )

    api_client.force_authenticate(user=therapist.user)
    url: str = reverse('document-download', kwargs={'pk': doc.id})

    try:
        response: object = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.getvalue() == b'%PDF-1.4 therapist access'
    finally:
        if file_path.exists():
            file_path.unlink()


@pytest.mark.django_db
def test_other_therapist_cannot_download_document(
    api_client: object, patient: object, therapist: object, therapist_b: object,
) -> None:
    """Sprawdza odrzucenie próby pobrania dokumentu przez obcego fizjoterapeutę (BOLA)."""
    # Arrange
    doc: MedicalDocument = MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Tajny Dokument',
        file_url='/media/documents/secret.pdf',
        mime_type='application/pdf',
    )

    api_client.force_authenticate(user=therapist_b.user)
    url: str = reverse('document-download', kwargs={'pk': doc.id})

    response: object = api_client.get(url)
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_nonexistent_document_returns_404(api_client: object, patient: object) -> None:
    """Sprawdza zwrócenie statusu 404 dla nieistniejącego dokumentu medycznego."""
    # Arrange
    api_client.force_authenticate(user=patient.user)
    import uuid
    url: str = reverse('document-download', kwargs={'pk': uuid.uuid4()})

    response: object = api_client.get(url)
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_download_prevents_directory_traversal(
    api_client: object, patient: object, therapist: object,
) -> None:
    """Sprawdza odrzucenie prób pobrania pliku poza dozwolonym katalogiem media (Directory Traversal)."""
    # Arrange
    doc: MedicalDocument = MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Traversal Attempt',
        file_url='/media/../settings.py',
        mime_type='application/pdf',
    )

    api_client.force_authenticate(user=patient.user)
    url: str = reverse('document-download', kwargs={'pk': doc.id})

    response: object = api_client.get(url)
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_download_missing_file_on_disk_returns_404(
    api_client: object, patient: object, therapist: object,
) -> None:
    """Sprawdza zwrócenie statusu 404 w przypadku braku pliku na dysku dla istniejącego rekordu baza danych."""
    # Arrange
    doc: MedicalDocument = MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Missing Disk File',
        file_url='/media/documents/non_existent_file_xyz.pdf',
        mime_type='application/pdf',
    )

    api_client.force_authenticate(user=patient.user)
    url: str = reverse('document-download', kwargs={'pk': doc.id})

    response: object = api_client.get(url)
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND

