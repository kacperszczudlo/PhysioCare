import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from core.storage import save_upload, validate_upload_file


def test_validate_upload_file_rejects_disallowed_mime_type() -> None:
    """Sprawdza odrzucenie pliku z niedozwolonym typem MIME (np. plik wykonywalny exe/sh)."""
    # Arrange
    fake_exe: SimpleUploadedFile = SimpleUploadedFile(
        'malware.exe', b'MZExecutableBinaryData', content_type='application/x-msdownload'
    )

    # Act & Assert
    with pytest.raises(ValidationError, match='Niedozwolony typ pliku'):
        validate_upload_file(
            fake_exe,
            allowed_mime={'application/pdf', 'image/jpeg'},
        )


def test_validate_upload_file_rejects_exceeding_file_size_limit() -> None:
    """Sprawdza odrzucenie pliku przekraczającego ustalony maksymalny rozmiar w bajtach."""
    # Arrange
    large_content: bytes = b'A' * (2 * 1024 * 1024)  # 2 MB
    large_pdf: SimpleUploadedFile = SimpleUploadedFile(
        'large.pdf', b'%PDF-1.4 ' + large_content, content_type='application/pdf'
    )

    # Act & Assert
    with pytest.raises(ValidationError, match='przekracza limit'):
        validate_upload_file(
            large_pdf,
            allowed_mime={'application/pdf'},
            max_bytes=1024 * 1024,  # Limit 1 MB
            label='Dokument medyczny',
        )


def test_validate_upload_file_type_checks() -> None:
    """Weryfikuje zgłaszanie wyjątku TypeError dla nieprawidłowych typów argumentów w validate_upload_file."""
    # Act & Assert
    with pytest.raises(TypeError, match="Argument 'uploaded_file' nie może być None."):
        validate_upload_file(None)

    with pytest.raises(TypeError, match="Argument 'allowed_mime' musi być typu set"):
        validate_upload_file(SimpleUploadedFile('test.pdf', b'%PDF-1.4'), allowed_mime=['application/pdf'])  # type: ignore[arg-type]


def test_save_upload_type_checks() -> None:
    """Weryfikuje zgłaszanie wyjątku TypeError dla nieprawidłowych typów argumentów w save_upload."""
    # Act & Assert
    with pytest.raises(TypeError, match="Argument 'uploaded_file' nie może być None."):
        save_upload(None, subdir='documents')

    with pytest.raises(TypeError, match="Argument 'subdir' musi być typu str."):
        save_upload(SimpleUploadedFile('test.pdf', b'%PDF-1.4'), subdir=123)  # type: ignore[arg-type]
