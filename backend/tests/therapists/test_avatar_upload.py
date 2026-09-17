from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

if TYPE_CHECKING:
    from pytest_django.fixtures import SettingsWrapper
    from patients.models import PatientProfile
    from therapists.models import TherapistProfile


def _png_bytes() -> bytes:
    """Zwraca surowe bajty minimalnego obrazu PNG do testów."""
    return (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00'
        b'\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    )


@pytest.mark.django_db
def test_therapist_can_upload_avatar(
    therapist: 'TherapistProfile',
    settings: 'SettingsWrapper',
    tmp_path: Path,
) -> None:
    """Sprawdza pomyślne przesłanie pliku awatara przez fizjoterapeutę."""
    # Arrange
    settings.MEDIA_ROOT = tmp_path
    client: APIClient = APIClient()
    client.force_authenticate(user=therapist.user)

    upload: SimpleUploadedFile = SimpleUploadedFile(
        'avatar.png',
        _png_bytes(),
        content_type='image/png',
    )
    # Act
    response = client.post(
        '/api/v1/therapist/profile/avatar/',
        {'file': upload},
        format='multipart',
    )

    # Assert
    assert response.status_code == 200
    assert response.data['avatar_url'].startswith('/media/avatars/')
    therapist.refresh_from_db()
    assert therapist.avatar_url == response.data['avatar_url']
    assert (tmp_path / response.data['avatar_url'].removeprefix('/media/')).is_file()


@pytest.mark.django_db
def test_patient_can_upload_avatar(
    patient: 'PatientProfile',
    settings: 'SettingsWrapper',
    tmp_path: Path,
) -> None:
    """Sprawdza pomyślne przesłanie pliku awatara przez pacjenta."""
    # Arrange
    settings.MEDIA_ROOT = tmp_path
    client: APIClient = APIClient()
    client.force_authenticate(user=patient.user)

    upload: SimpleUploadedFile = SimpleUploadedFile(
        'me.png',
        _png_bytes(),
        content_type='image/png',
    )
    # Act
    response = client.post(
        '/api/v1/me/profile/avatar/',
        {'file': upload},
        format='multipart',
    )

    # Assert
    assert response.status_code == 200
    assert response.data['avatar_url'].startswith('/media/avatars/')
    patient.refresh_from_db()
    assert patient.avatar_url == response.data['avatar_url']


@pytest.mark.django_db
def test_avatar_rejects_pdf(
    therapist: 'TherapistProfile',
    settings: 'SettingsWrapper',
    tmp_path: Path,
) -> None:
    """Sprawdza odrzucenie pliku PDF przesłanego jako awatar."""
    # Arrange
    settings.MEDIA_ROOT = tmp_path
    client: APIClient = APIClient()
    client.force_authenticate(user=therapist.user)

    upload: SimpleUploadedFile = SimpleUploadedFile(
        'doc.pdf',
        b'%PDF-1.4 fake',
        content_type='application/pdf',
    )
    # Act
    response = client.post(
        '/api/v1/therapist/profile/avatar/',
        {'file': upload},
        format='multipart',
    )

    # Assert
    assert response.status_code == 400


@pytest.mark.django_db
def test_avatar_rejects_pdf_bytes_labeled_as_png(
    therapist: 'TherapistProfile',
    settings: 'SettingsWrapper',
    tmp_path: Path,
) -> None:
    """Sprawdza wykrycie fałszywego rozszerzenia PNG przy zawartości pliku PDF."""
    # Arrange
    settings.MEDIA_ROOT = tmp_path
    client: APIClient = APIClient()
    client.force_authenticate(user=therapist.user)

    upload: SimpleUploadedFile = SimpleUploadedFile(
        'avatar.png',
        b'%PDF-1.4 spoofed',
        content_type='image/png',
    )
    # Act
    response = client.post(
        '/api/v1/therapist/profile/avatar/',
        {'file': upload},
        format='multipart',
    )

    # Assert
    assert response.status_code == 400


@pytest.mark.django_db
def test_avatar_requires_file(therapist: 'TherapistProfile') -> None:
    """Sprawdza zgłoszenie błędu przy braku pliku w żądaniu aktualizacji awatara."""
    # Arrange
    client: APIClient = APIClient()
    client.force_authenticate(user=therapist.user)
    # Act
    response = client.post('/api/v1/therapist/profile/avatar/', {}, format='multipart')
    # Assert
    assert response.status_code == 400
    assert response.data['error']['code'] == 'FILE_REQUIRED'

