MIME_PNG: str = 'image/png'
MIME_JPEG: str = 'image/jpeg'
MIME_WEBP: str = 'image/webp'
MIME_PDF: str = 'application/pdf'
MIME_MP4: str = 'video/mp4'

SNIFF_BYTES: int = 32

MIN_WEBP_HEADER_BYTES: int = 12
RIFF_WEBP_OFFSET_START: int = 8
RIFF_WEBP_OFFSET_END: int = 12

MIN_MP4_HEADER_BYTES: int = 8
FTYP_MP4_OFFSET_START: int = 4
FTYP_MP4_OFFSET_END: int = 8


def sniff_bytes(head: bytes) -> str:
    """Rozpoznaje typ MIME na podstawie pierwszych bajtów nagłówka pliku.

    Args:
        head (bytes): Początkowe bajty zawartości pliku.

    Returns:
        str: Wykryty typ MIME pliku lub pusty ciąg znaków.

    Raises:
        TypeError: Gdy head nie jest typu bytes lub bytearray.
    """
    if not isinstance(head, (bytes, bytearray)):
        raise TypeError("Argument 'head' musi być typu bytes.")

    raw_bytes = bytes(head)
    if raw_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
        return MIME_PNG
    if raw_bytes.startswith(b'\xff\xd8\xff'):
        return MIME_JPEG
    if raw_bytes.startswith(b'%PDF'):
        return MIME_PDF
    if (
        len(raw_bytes) >= MIN_WEBP_HEADER_BYTES
        and raw_bytes.startswith(b'RIFF')
        and raw_bytes[RIFF_WEBP_OFFSET_START:RIFF_WEBP_OFFSET_END] == b'WEBP'
    ):
        return MIME_WEBP
    if (
        len(raw_bytes) >= MIN_MP4_HEADER_BYTES
        and raw_bytes[FTYP_MP4_OFFSET_START:FTYP_MP4_OFFSET_END] == b'ftyp'
    ):
        return MIME_MP4
    return ''


def sniff_upload_mime(uploaded_file: object) -> str:
    """Wykrywa typ MIME przesłanego pliku na podstawie jego sygnatury bajtowej.

    Args:
        uploaded_file (object): Obiekt przesłanego pliku Django.

    Returns:
        str: Wykryty typ MIME pliku lub pusty ciąg znaków.

    Raises:
        TypeError: Gdy uploaded_file jest None.
    """
    if uploaded_file is None:
        raise TypeError("Argument 'uploaded_file' nie może być None.")

    position = uploaded_file.tell() if hasattr(uploaded_file, 'tell') else 0
    head = uploaded_file.read(SNIFF_BYTES) if hasattr(uploaded_file, 'read') else b''
    if hasattr(uploaded_file, 'seek'):
        uploaded_file.seek(position)
    if isinstance(head, str):
        head = head.encode('latin-1', errors='ignore')
    return sniff_bytes(head)

