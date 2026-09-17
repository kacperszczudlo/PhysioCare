import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError

from core.file_magic import sniff_upload_mime

ALLOWED_UPLOAD_MIME: set[str] = {
    'application/pdf',
    'video/mp4',
}

ALLOWED_AVATAR_MIME: set[str] = {
    'image/jpeg',
    'image/png',
    'image/webp',
}

AVATAR_EXTENSIONS: dict[str, str] = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/webp': '.webp',
}

MIME_EXTENSIONS: dict[str, str] = {
    **AVATAR_EXTENSIONS,
    'application/pdf': '.pdf',
    'video/mp4': '.mp4',
}


def validate_upload_file(
    uploaded_file: object,
    *,
    allowed_mime: set[str] | None = None,
    max_bytes: int | None = None,
    label: str = 'Plik',
) -> str:
    """Waliduje typ MIME oraz rozmiar przesłanego pliku.

    Args:
        uploaded_file (object): Przesłany plik Django (UploadedFile).
        allowed_mime (set[str] | None): Zbiór dozwolonych typów MIME.
        max_bytes (int | None): Maksymalny dopuszczalny rozmiar pliku w bajtach.
        label (str): Etykieta pliku używana w komunikatach błędów.

    Returns:
        str: Wykryty typ MIME pliku.

    Raises:
        ValidationError: Gdy plik nie spełnia kryteriów formatu lub rozmiaru.
        TypeError: Gdy któryś z argumentów ma nieprawidłowy typ.
    """
    if uploaded_file is None:
        raise TypeError("Argument 'uploaded_file' nie może być None.")
    if allowed_mime is not None and not isinstance(allowed_mime, set):
        raise TypeError("Argument 'allowed_mime' musi być typu set[str] lub None.")
    if max_bytes is not None and not isinstance(max_bytes, int):
        raise TypeError("Argument 'max_bytes' musi być typu int lub None.")
    if not isinstance(label, str):
        raise TypeError("Argument 'label' musi być typu str.")

    allowed = allowed_mime if allowed_mime is not None else ALLOWED_UPLOAD_MIME
    sniffed = sniff_upload_mime(uploaded_file)
    if sniffed not in allowed:
        allowed_label = ', '.join(sorted(allowed))
        raise ValidationError(
            f'Niedozwolony typ pliku: {sniffed or "nieznany"}. Dozwolone: {allowed_label}.'
        )
    limit = max_bytes if max_bytes is not None else settings.DATA_UPLOAD_MAX_MEMORY_SIZE
    file_size = uploaded_file.size if hasattr(uploaded_file, 'size') else 0
    if file_size > limit:
        limit_mb = max(1, limit // (1024 * 1024))
        raise ValidationError(f'{label} przekracza limit {limit_mb} MB.')
    return sniffed


def save_upload(
    uploaded_file: object,
    *,
    subdir: str,
    allowed_mime: set[str] | None = None,
    max_bytes: int | None = None,
    label: str = 'Plik',
    force_ext: str | None = None,
) -> tuple[str, str]:
    """Zapisuje przesłany plik w wyznaczonym podkatalogu katalogu mediów.

    Args:
        uploaded_file (object): Przesłany plik Django.
        subdir (str): Nazwa podkatalogu w katalogu mediów.
        allowed_mime (set[str] | None): Zbiór akceptowalnych typów MIME.
        max_bytes (int | None): Maksymalny rozmiar pliku.
        label (str): Etykieta dla komunikatów błędów.
        force_ext (str | None): Opcjonalne narzucone rozszerzenie pliku.

    Returns:
        tuple[str, str]: Para (względny URL pliku, wykryty typ MIME).

    Raises:
        TypeError: Gdy któryś z argumentów ma nieprawidłowy typ.
    """
    if uploaded_file is None:
        raise TypeError("Argument 'uploaded_file' nie może być None.")
    if not isinstance(subdir, str):
        raise TypeError("Argument 'subdir' musi być typu str.")
    if allowed_mime is not None and not isinstance(allowed_mime, set):
        raise TypeError("Argument 'allowed_mime' musi być typu set[str] lub None.")
    if max_bytes is not None and not isinstance(max_bytes, int):
        raise TypeError("Argument 'max_bytes' musi być typu int lub None.")
    if not isinstance(label, str):
        raise TypeError("Argument 'label' musi być typu str.")
    if force_ext is not None and not isinstance(force_ext, str):
        raise TypeError("Argument 'force_ext' musi być typu str lub None.")

    sniffed = validate_upload_file(
        uploaded_file,
        allowed_mime=allowed_mime,
        max_bytes=max_bytes,
        label=label,
    )
    media_root = settings.MEDIA_ROOT if hasattr(settings, 'MEDIA_ROOT') else None
    if not media_root:
        media_root = settings.BASE_DIR / 'media'
        os.makedirs(media_root, exist_ok=True)

    if force_ext:
        ext = force_ext if force_ext.startswith('.') else f'.{force_ext}'
    else:
        file_name = uploaded_file.name if hasattr(uploaded_file, 'name') else ''
        ext = MIME_EXTENSIONS.get(sniffed) or os.path.splitext(file_name)[1].lower()
        if not ext:
            ext = MIME_EXTENSIONS.get(sniffed, '.bin')

    filename = f'{uuid.uuid4()}{ext}'
    target_dir = os.path.join(str(media_root), subdir)
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, filename)

    chunks = uploaded_file.chunks() if hasattr(uploaded_file, 'chunks') else []
    with open(target_path, 'wb+') as destination:
        for chunk in chunks:
            destination.write(chunk)

    return f'/media/{subdir}/{filename}', sniffed


def delete_media_url(file_url: str | None) -> None:
    """Usuwa lokalny plik multimedialny wskazywany przez adres URL `/media/...`.

    Args:
        file_url (str | None): Względny adres URL pliku do usunięcia.

    Raises:
        TypeError: Gdy file_url nie jest napisem ani None.
    """
    if file_url is not None and not isinstance(file_url, str):
        raise TypeError("Argument 'file_url' musi być typu str lub None.")

    if not file_url or not file_url.startswith('/media/'):
        return
    relative = file_url.removeprefix('/media/')
    media_root = settings.MEDIA_ROOT if hasattr(settings, 'MEDIA_ROOT') else ''
    path = os.path.join(str(media_root), relative)
    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass


def save_avatar(uploaded_file: object, *, previous_url: str = '') -> str:
    """Zapisuje nowy obraz awatara i opcjonalnie usuwa poprzedni plik.

    Args:
        uploaded_file (object): Przesłany plik graficzny awatara.
        previous_url (str): Adres URL poprzedniego awatara do usunięcia.

    Returns:
        str: Adres URL nowo zapisanego awatara.

    Raises:
        TypeError: Gdy uploaded_file jest None lub previous_url nie jest napisem.
    """
    if uploaded_file is None:
        raise TypeError("Argument 'uploaded_file' nie może być None.")
    if not isinstance(previous_url, str):
        raise TypeError("Argument 'previous_url' musi być typu str.")

    max_mb = settings.MAX_AVATAR_MB if hasattr(settings, 'MAX_AVATAR_MB') else 5
    max_bytes = max_mb * 1024 * 1024
    url, _sniffed = save_upload(
        uploaded_file,
        subdir='avatars',
        allowed_mime=ALLOWED_AVATAR_MIME,
        max_bytes=max_bytes,
        label='Avatar',
    )
    if previous_url and previous_url != url:
        delete_media_url(previous_url)
    return url


