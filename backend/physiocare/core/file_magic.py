"""Sniff MIME from file magic bytes - do not trust the client Content-Type."""

MIME_PNG = 'image/png'
MIME_JPEG = 'image/jpeg'
MIME_WEBP = 'image/webp'
MIME_PDF = 'application/pdf'
MIME_MP4 = 'video/mp4'

SNIFF_BYTES = 32

MIN_WEBP_HEADER_BYTES = 12
RIFF_WEBP_OFFSET_START = 8
RIFF_WEBP_OFFSET_END = 12

MIN_MP4_HEADER_BYTES = 8
FTYP_MP4_OFFSET_START = 4
FTYP_MP4_OFFSET_END = 8


def sniff_bytes(head: bytes) -> str:
    if head.startswith(b'\x89PNG\r\n\x1a\n'):
        return MIME_PNG
    if head.startswith(b'\xff\xd8\xff'):
        return MIME_JPEG
    if head.startswith(b'%PDF'):
        return MIME_PDF
    if (
        len(head) >= MIN_WEBP_HEADER_BYTES
        and head.startswith(b'RIFF')
        and head[RIFF_WEBP_OFFSET_START:RIFF_WEBP_OFFSET_END] == b'WEBP'
    ):
        return MIME_WEBP
    if (
        len(head) >= MIN_MP4_HEADER_BYTES
        and head[FTYP_MP4_OFFSET_START:FTYP_MP4_OFFSET_END] == b'ftyp'
    ):
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
