"""Sniff MIME from file magic bytes — do not trust the client Content-Type."""

MIME_PNG = 'image/png'
MIME_JPEG = 'image/jpeg'
MIME_WEBP = 'image/webp'
MIME_PDF = 'application/pdf'
MIME_MP4 = 'video/mp4'

SNIFF_BYTES = 32


def sniff_bytes(head: bytes) -> str:
    if head.startswith(b'\x89PNG\r\n\x1a\n'):
        return MIME_PNG
    if head.startswith(b'\xff\xd8\xff'):
        return MIME_JPEG
    if head.startswith(b'%PDF'):
        return MIME_PDF
    if len(head) >= 12 and head.startswith(b'RIFF') and head[8:12] == b'WEBP':
        return MIME_WEBP
    if len(head) >= 8 and head[4:8] == b'ftyp':
        return MIME_MP4
    return ''


def sniff_upload_mime(uploaded_file) -> str:
    """Return sniffed MIME or empty string when the signature is unknown."""
    position = uploaded_file.tell()
    head = uploaded_file.read(SNIFF_BYTES) or b''
    uploaded_file.seek(position)
    if isinstance(head, str):
        head = head.encode('latin-1', errors='ignore')
    return sniff_bytes(head)
