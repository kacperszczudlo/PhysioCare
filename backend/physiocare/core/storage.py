import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError

ALLOWED_UPLOAD_MIME = {
    'application/pdf',
    'video/mp4',
}

ALLOWED_AVATAR_MIME = {
    'image/jpeg',
    'image/png',
    'image/webp',
}

AVATAR_EXTENSIONS = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/webp': '.webp',
}


def validate_upload_file(uploaded_file, *, allowed_mime=None, max_bytes=None, label='Plik'):
    allowed = allowed_mime if allowed_mime is not None else ALLOWED_UPLOAD_MIME
    content_type = getattr(uploaded_file, 'content_type', '') or ''
    if content_type not in allowed:
        allowed_label = ', '.join(sorted(allowed))
        raise ValidationError(
            f'Niedozwolony typ pliku: {content_type or "nieznany"}. Dozwolone: {allowed_label}.'
        )
    limit = max_bytes if max_bytes is not None else settings.DATA_UPLOAD_MAX_MEMORY_SIZE
    if uploaded_file.size > limit:
        limit_mb = max(1, limit // (1024 * 1024))
        raise ValidationError(f'{label} przekracza limit {limit_mb} MB.')


def save_upload(
    uploaded_file,
    *,
    subdir: str,
    allowed_mime=None,
    max_bytes=None,
    label='Plik',
    force_ext=None,
) -> str:
    validate_upload_file(
        uploaded_file,
        allowed_mime=allowed_mime,
        max_bytes=max_bytes,
        label=label,
    )
    media_root = getattr(settings, 'MEDIA_ROOT', None)
    if not media_root:
        media_root = settings.BASE_DIR / 'media'
        os.makedirs(media_root, exist_ok=True)

    if force_ext:
        ext = force_ext if force_ext.startswith('.') else f'.{force_ext}'
    else:
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if not ext and allowed_mime is ALLOWED_AVATAR_MIME:
            content_type = getattr(uploaded_file, 'content_type', '')
            ext = AVATAR_EXTENSIONS.get(content_type, '.jpg')

    filename = f'{uuid.uuid4()}{ext}'
    target_dir = os.path.join(str(media_root), subdir)
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, filename)

    with open(target_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    return f'/media/{subdir}/{filename}'


def delete_media_url(file_url: str | None) -> None:
    """Best-effort delete of a local /media/... file."""
    if not file_url or not file_url.startswith('/media/'):
        return
    relative = file_url.removeprefix('/media/')
    path = os.path.join(str(settings.MEDIA_ROOT), relative)
    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass


def save_avatar(uploaded_file, *, previous_url: str = '') -> str:
    max_bytes = getattr(settings, 'MAX_AVATAR_MB', 5) * 1024 * 1024
    content_type = getattr(uploaded_file, 'content_type', '') or ''
    force_ext = AVATAR_EXTENSIONS.get(content_type)
    url = save_upload(
        uploaded_file,
        subdir='avatars',
        allowed_mime=ALLOWED_AVATAR_MIME,
        max_bytes=max_bytes,
        label='Avatar',
        force_ext=force_ext,
    )
    if previous_url and previous_url != url:
        delete_media_url(previous_url)
    return url
