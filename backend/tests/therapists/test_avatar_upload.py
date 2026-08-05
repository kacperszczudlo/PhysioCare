import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient


def _png_bytes() -> bytes:
    return (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00'
        b'\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    )


@pytest.mark.django_db
def test_therapist_can_upload_avatar(therapist, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    client = APIClient()
    client.force_authenticate(user=therapist.user)

    upload = SimpleUploadedFile(
        'avatar.png',
        _png_bytes(),
        content_type='image/png',
    )
    response = client.post(
        '/api/v1/therapist/profile/avatar/',
        {'file': upload},
        format='multipart',
    )

    assert response.status_code == 200
    assert response.data['avatar_url'].startswith('/media/avatars/')
    therapist.refresh_from_db()
    assert therapist.avatar_url == response.data['avatar_url']
    assert (tmp_path / response.data['avatar_url'].removeprefix('/media/')).is_file()


@pytest.mark.django_db
def test_patient_can_upload_avatar(patient, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    client = APIClient()
    client.force_authenticate(user=patient.user)

    upload = SimpleUploadedFile(
        'me.png',
        _png_bytes(),
        content_type='image/png',
    )
    response = client.post(
        '/api/v1/me/profile/avatar/',
        {'file': upload},
        format='multipart',
    )

    assert response.status_code == 200
    assert response.data['avatar_url'].startswith('/media/avatars/')
    patient.refresh_from_db()
    assert patient.avatar_url == response.data['avatar_url']


@pytest.mark.django_db
def test_avatar_rejects_pdf(therapist, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    client = APIClient()
    client.force_authenticate(user=therapist.user)

    upload = SimpleUploadedFile(
        'doc.pdf',
        b'%PDF-1.4 fake',
        content_type='application/pdf',
    )
    response = client.post(
        '/api/v1/therapist/profile/avatar/',
        {'file': upload},
        format='multipart',
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_avatar_requires_file(therapist):
    client = APIClient()
    client.force_authenticate(user=therapist.user)
    response = client.post('/api/v1/therapist/profile/avatar/', {}, format='multipart')
    assert response.status_code == 400
    assert response.data['error']['code'] == 'FILE_REQUIRED'
