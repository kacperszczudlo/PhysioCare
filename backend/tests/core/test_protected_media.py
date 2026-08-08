import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from documents.models import MedicalDocument
from exercises.models import Exercise, ExerciseAssignment, MediaType


def _auth(client, user):
    token = str(RefreshToken.for_user(user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')


@pytest.mark.django_db
def test_media_requires_authentication(api_client, tmp_path, settings, therapist, patient):
    settings.MEDIA_ROOT = tmp_path
    documents_dir = tmp_path / 'documents'
    documents_dir.mkdir()
    file_path = documents_dir / 'secret.pdf'
    file_path.write_bytes(b'%PDF-1.4 secret')

    MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Tajny',
        file_url='/media/documents/secret.pdf',
        mime_type='application/pdf',
    )

    response = api_client.get('/media/documents/secret.pdf')
    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


@pytest.mark.django_db
def test_media_document_owner_can_download(api_client, tmp_path, settings, therapist, patient):
    settings.MEDIA_ROOT = tmp_path
    documents_dir = tmp_path / 'documents'
    documents_dir.mkdir()
    file_path = documents_dir / 'ok.pdf'
    file_path.write_bytes(b'%PDF-1.4 ok')

    MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='OK',
        file_url='/media/documents/ok.pdf',
        mime_type='application/pdf',
    )

    _auth(api_client, patient.user)
    response = api_client.get('/media/documents/ok.pdf')
    assert response.status_code == status.HTTP_200_OK
    assert b'%PDF-1.4 ok' in b''.join(response.streaming_content)


@pytest.mark.django_db
def test_media_document_foreign_user_gets_404(
    api_client, tmp_path, settings, therapist, therapist_b, patient,
):
    settings.MEDIA_ROOT = tmp_path
    documents_dir = tmp_path / 'documents'
    documents_dir.mkdir()
    file_path = documents_dir / 'private.pdf'
    file_path.write_bytes(b'%PDF-1.4 private')

    MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Private',
        file_url='/media/documents/private.pdf',
        mime_type='application/pdf',
    )

    _auth(api_client, therapist_b.user)
    response = api_client.get('/media/documents/private.pdf')
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_media_exercise_assigned_patient_can_access(
    api_client, tmp_path, settings, therapist, patient,
):
    settings.MEDIA_ROOT = tmp_path
    exercises_dir = tmp_path / 'exercises'
    exercises_dir.mkdir()
    file_path = exercises_dir / 'clip.mp4'
    file_path.write_bytes(b'fake-mp4')

    today = timezone.localdate()
    exercise = Exercise.objects.create(
        therapist=therapist,
        title='Mostek',
        media_type=MediaType.VIDEO,
        file_url='/media/exercises/clip.mp4',
    )
    ExerciseAssignment.objects.create(
        exercise=exercise,
        patient=patient,
        dosage='3x10',
        start_date=today,
        end_date=today,
    )

    _auth(api_client, patient.user)
    response = api_client.get('/media/exercises/clip.mp4')
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_media_rejects_path_traversal(api_client, therapist):
    _auth(api_client, therapist.user)
    response = api_client.get('/media/../settings.py')
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_document_download_endpoint_still_works(
    api_client, tmp_path, settings, therapist, patient,
):
    settings.MEDIA_ROOT = tmp_path
    documents_dir = tmp_path / 'documents'
    documents_dir.mkdir()
    (documents_dir / 'doc.pdf').write_bytes(b'%PDF-1.4 download')

    document = MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Download',
        file_url='/media/documents/doc.pdf',
        mime_type='application/pdf',
    )

    _auth(api_client, patient.user)
    url = reverse('document-download', kwargs={'pk': document.id})
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
