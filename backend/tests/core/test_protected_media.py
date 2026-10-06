import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from documents.models import MedicalDocument
from exercises.models import Exercise, ExerciseAssignment, MediaType


def _auth(client: object, user: object) -> None:
    """Ustawia nagłówek autoryzacji Bearer JWT dla klienta testowego API."""
    token: str = str(RefreshToken.for_user(user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')


@pytest.mark.django_db
def test_media_requires_authentication(
    api_client: object, tmp_path: object, settings: object, therapist: object, patient: object,
) -> None:
    """Sprawdza, czy dostęp do zasobów chronionych wymaga uwierzytelnienia."""
    # Arrange
    settings.MEDIA_ROOT = tmp_path
    documents_dir: object = tmp_path / 'documents'
    documents_dir.mkdir()
    file_path: object = documents_dir / 'secret.pdf'
    file_path.write_bytes(b'%PDF-1.4 secret')

    MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Tajny',
        file_url='/media/documents/secret.pdf',
        mime_type='application/pdf',
    )

    response: object = api_client.get('/media/documents/secret.pdf')
    # Assert
    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


@pytest.mark.django_db
def test_media_document_owner_can_download(
    api_client: object, tmp_path: object, settings: object, therapist: object, patient: object,
) -> None:
    """Sprawdza, czy właściciel dokumentu medycznego (pacjent) może go pobrać."""
    # Arrange
    settings.MEDIA_ROOT = tmp_path
    documents_dir: object = tmp_path / 'documents'
    documents_dir.mkdir()
    file_path: object = documents_dir / 'ok.pdf'
    file_path.write_bytes(b'%PDF-1.4 ok')

    MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='OK',
        file_url='/media/documents/ok.pdf',
        mime_type='application/pdf',
    )

    _auth(api_client, patient.user)
    response: object = api_client.get('/media/documents/ok.pdf')
    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert b'%PDF-1.4 ok' in b''.join(response.streaming_content)


@pytest.mark.django_db
def test_media_document_foreign_user_gets_404(
    api_client: object, tmp_path: object, settings: object, therapist: object, therapist_b: object, patient: object,
) -> None:
    """Sprawdza, czy obcy użytkownik otrzymuje status 404 przy próbie pobrania cudzego dokumentu (BOLA)."""
    # Arrange
    settings.MEDIA_ROOT = tmp_path
    documents_dir: object = tmp_path / 'documents'
    documents_dir.mkdir()
    file_path: object = documents_dir / 'private.pdf'
    file_path.write_bytes(b'%PDF-1.4 private')

    MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Private',
        file_url='/media/documents/private.pdf',
        mime_type='application/pdf',
    )

    _auth(api_client, therapist_b.user)
    response: object = api_client.get('/media/documents/private.pdf')
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_media_exercise_assigned_patient_can_access(
    api_client: object, tmp_path: object, settings: object, therapist: object, patient: object,
) -> None:
    """Sprawdza, czy pacjent ma dostęp do pliku wideo ćwiczenia, które zostało mu przypisane."""
    # Arrange
    settings.MEDIA_ROOT = tmp_path
    exercises_dir: object = tmp_path / 'exercises'
    exercises_dir.mkdir()
    file_path: object = exercises_dir / 'clip.mp4'
    file_path.write_bytes(b'fake-mp4')

    today: object = timezone.localdate()
    exercise: Exercise = Exercise.objects.create(
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
    response: object = api_client.get('/media/exercises/clip.mp4')
    # Assert
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_media_rejects_path_traversal(api_client: object, therapist: object) -> None:
    """Sprawdza odrzucenie prób ataku typu Path Traversal przy pobieraniu plików z katalogu media."""
    # Arrange
    _auth(api_client, therapist.user)
    response: object = api_client.get('/media/../settings.py')
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_document_download_endpoint_still_works(
    api_client: object, tmp_path: object, settings: object, therapist: object, patient: object,
) -> None:
    """Sprawdza działanie dedykowanego punktu końcowego pobierania dokumentów medycznych."""
    # Arrange
    settings.MEDIA_ROOT = tmp_path
    documents_dir: object = tmp_path / 'documents'
    documents_dir.mkdir()
    (documents_dir / 'doc.pdf').write_bytes(b'%PDF-1.4 download')

    document: MedicalDocument = MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Download',
        file_url='/media/documents/doc.pdf',
        mime_type='application/pdf',
    )

    _auth(api_client, patient.user)
    url: str = reverse('document-download', kwargs={'pk': document.id})
    response: object = api_client.get(url)
    # Assert
    assert response.status_code == status.HTTP_200_OK


def _write_avatar(tmp_path: object, name: str = 'face.png') -> str:
    """Tworzy testowy plik awatara w katalogu tymczasowym i zwraca jego URL."""
    avatars_dir: object = tmp_path / 'avatars'
    avatars_dir.mkdir(exist_ok=True)
    (avatars_dir / name).write_bytes(b'fake-png')
    return f'/media/avatars/{name}'


@pytest.mark.django_db
def test_media_patient_avatar_owner_and_therapist_can_access(
    api_client: object, tmp_path: object, settings: object, therapist: object, patient: object,
) -> None:
    """Sprawdza, czy właściciel awatara oraz jego fizjoterapeuta mogą uzyskać dostęp do awatara pacjenta."""
    # Arrange
    settings.MEDIA_ROOT = tmp_path
    patient.avatar_url = _write_avatar(tmp_path, 'patient.png')
    patient.save(update_fields=['avatar_url'])

    _auth(api_client, patient.user)
    # Assert
    assert api_client.get(patient.avatar_url).status_code == status.HTTP_200_OK

    _auth(api_client, therapist.user)
    assert api_client.get(patient.avatar_url).status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_media_patient_avatar_foreign_therapist_gets_404(
    api_client: object, tmp_path: object, settings: object, therapist_b: object, patient: object,
) -> None:
    """Sprawdza, czy obcy fizjoterapeuta otrzymuje 404 przy próbie pobrania awatara nieprzipisanego pacjenta."""
    # Arrange
    settings.MEDIA_ROOT = tmp_path
    patient.avatar_url = _write_avatar(tmp_path, 'private-patient.png')
    patient.save(update_fields=['avatar_url'])

    _auth(api_client, therapist_b.user)
    # Assert
    assert api_client.get(patient.avatar_url).status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_media_therapist_avatar_linked_patient_can_access(
    api_client: object, tmp_path: object, settings: object, therapist: object, patient: object,
) -> None:
    """Sprawdza, czy powiązany pacjent ma dostęp do awatara swojego fizjoterapeuty."""
    # Arrange
    settings.MEDIA_ROOT = tmp_path
    therapist.avatar_url = _write_avatar(tmp_path, 'therapist.png')
    therapist.save(update_fields=['avatar_url'])

    _auth(api_client, patient.user)
    # Assert
    assert api_client.get(therapist.avatar_url).status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_media_orphan_avatar_denied(api_client: object, tmp_path: object, settings: object, therapist: object) -> None:
    """Sprawdza odrzucenie próby dostępu do niepowiązanego/sierocego pliku awatara."""
    # Arrange
    settings.MEDIA_ROOT = tmp_path
    orphan_url: str = _write_avatar(tmp_path, 'orphan.png')

    _auth(api_client, therapist.user)
    # Assert
    assert api_client.get(orphan_url).status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_protected_media_and_documents_prevent_cdn_caching(
    api_client: object, tmp_path: object, settings: object, therapist: object, patient: object,
) -> None:
    """Weryfikuje, czy pliki medyczne posiadają nagłówki zabraniające buforowania przez CDN i proxy."""
    # Arrange
    settings.MEDIA_ROOT = tmp_path
    documents_dir: object = tmp_path / 'documents'
    documents_dir.mkdir(exist_ok=True)
    file_path: object = documents_dir / 'clinical_record.pdf'
    file_path.write_bytes(b'%PDF-1.4 clinical')

    document = MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Clinical Record',
        file_url='/media/documents/clinical_record.pdf',
        mime_type='application/pdf',
    )

    _auth(api_client, patient.user)

    # Act & Assert 1: Bezpośredni dostęp do chronionego /media/...
    media_response = api_client.get('/media/documents/clinical_record.pdf')
    assert media_response.status_code == status.HTTP_200_OK
    assert media_response['Cache-Control'] == 'private, no-store'
    assert media_response['X-Content-Type-Options'] == 'nosniff'

    # Act & Assert 2: Endpoint pobierania dokumentu /api/v1/documents/<id>/download/
    download_url: str = reverse('document-download', kwargs={'pk': document.id})
    download_response = api_client.get(download_url)
    assert download_response.status_code == status.HTTP_200_OK
    assert download_response['Cache-Control'] == 'private, no-store'
    assert download_response['X-Content-Type-Options'] == 'nosniff'

