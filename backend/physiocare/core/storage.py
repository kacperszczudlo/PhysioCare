import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError


ALLOWED_UPLOAD_MIME = {
    'application/pdf',
    'video/mp4',
}


def validate_upload_file(uploaded_file):
    content_type = getattr(uploaded_file, 'content_type', '')
    if content_type not in ALLOWED_UPLOAD_MIME:
        raise ValidationError(
            f'Niedozwolony typ pliku: {content_type}. Dozwolone: PDF, MP4.'
        )
    max_bytes = settings.DATA_UPLOAD_MAX_MEMORY_SIZE
    if uploaded_file.size > max_bytes:
        raise ValidationError(
            f'Plik przekracza limit {settings.MAX_UPLOAD_MB} MB.'
        )


def save_upload(uploaded_file, *, subdir: str) -> str:
    validate_upload_file(uploaded_file)
    media_root = getattr(settings, 'MEDIA_ROOT', None)
    if not media_root:
        media_root = settings.BASE_DIR / 'media'
        os.makedirs(media_root, exist_ok=True)

    ext = os.path.splitext(uploaded_file.name)[1].lower()
    filename = f'{uuid.uuid4()}{ext}'
    target_dir = os.path.join(str(media_root), subdir)
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, filename)

    with open(target_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    return f'/media/{subdir}/{filename}'
