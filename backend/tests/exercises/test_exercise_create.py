from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status

from exercises.models import Exercise, MediaType


@pytest.mark.django_db
@patch('exercises.views.save_upload', return_value=('/media/exercises/test.mp4', 'video/mp4'))
def test_therapist_creates_exercise_with_file_successfully(
    mock_save: object, api_client: object, therapist: object,
) -> None:
    """Sprawdza pomyślne utworzenie ćwiczenia z plikiem wideo przez fizjoterapeutę."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)
    uploaded_file: SimpleUploadedFile = SimpleUploadedFile(
        'rotacjaBarkow.mp4',
        b'\x00\x00\x00\x20ftypmp42fake mp4 content',
        content_type='video/mp4',
    )

    # Act
    response: object = api_client.post(
        '/api/v1/therapist/exercises/',
        {
            'title': 'Rotacja zewnętrzna barku w uniesieniu (90°)',
            'media_type': MediaType.VIDEO,
            'instruction': '1. Stań prosto.\n2. Wykonaj rotację.',
            'file': uploaded_file,
        },
        format='multipart',
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['title'] == 'Rotacja zewnętrzna barku w uniesieniu (90°)'
    assert response.data['file_url'] == '/media/exercises/test.mp4'
    mock_save.assert_called_once()
    assert Exercise.objects.filter(therapist=therapist).count() == 1


@pytest.mark.django_db
def test_create_exercise_without_file_returns_400(
    api_client: object, therapist: object,
) -> None:
    """Sprawdza zwrócenie błędu 400 przy próbie utworzenia ćwiczenia bez wymaganego pliku."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)

    # Act
    response: object = api_client.post(
        '/api/v1/therapist/exercises/',
        {
            'title': 'Ćwiczenie bez pliku',
            'media_type': MediaType.VIDEO,
        },
        format='multipart',
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error']['code'] == 'VALIDATION'


@pytest.mark.django_db
@patch('exercises.views.save_upload', side_effect=DjangoValidationError('Niedozwolony typ pliku.'))
def test_create_exercise_with_invalid_file_type_returns_400(
    mock_save: object, api_client: object, therapist: object,
) -> None:
    """Sprawdza, że błąd walidacji pliku w save_upload zwraca kod 400 zamiast błędu 500."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)
    uploaded_file: SimpleUploadedFile = SimpleUploadedFile(
        'bad.exe', b'MZ fake binary', content_type='application/octet-stream'
    )

    # Act
    response: object = api_client.post(
        '/api/v1/therapist/exercises/',
        {
            'title': 'Zły plik',
            'media_type': MediaType.VIDEO,
            'file': uploaded_file,
        },
        format='multipart',
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'file' in response.data['error']['details']
