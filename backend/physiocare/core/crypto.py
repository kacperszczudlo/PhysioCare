import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

_FERNET_INSTANCE: Fernet | None = None


def get_fernet_key() -> bytes:
    """Return configured FIELD_ENCRYPTION_KEY or derive a stable key from SECRET_KEY."""
    key_str = os.environ.get('FIELD_ENCRYPTION_KEY', '').strip()
    if key_str:
        return key_str.encode('utf-8')

    secret = getattr(settings, 'SECRET_KEY', 'physiocare-default-encryption-secret-key-2026')
    derived = hashlib.sha256(secret.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(derived)


def get_fernet() -> Fernet:
    """Return singleton Fernet cipher instance."""
    global _FERNET_INSTANCE
    if _FERNET_INSTANCE is None:
        _FERNET_INSTANCE = Fernet(get_fernet_key())
    return _FERNET_INSTANCE


def reset_fernet_cache() -> None:
    """Reset cached Fernet instance (useful for testing key changes)."""
    global _FERNET_INSTANCE
    _FERNET_INSTANCE = None


def encrypt_value(value: str | None) -> str | None:
    """Encrypt plaintext string into Fernet ciphertext (gAAAAA...)."""
    if value is None or value == '':
        return value

    val_str = str(value)
    if val_str.startswith('gAAAAA'):
        return val_str

    f = get_fernet()
    return f.encrypt(val_str.encode('utf-8')).decode('utf-8')


def decrypt_value(value: str | None) -> str | None:
    """Decrypt Fernet ciphertext back to plaintext. Return unchanged if not encrypted."""
    if value is None or value == '':
        return value

    val_str = str(value)
    if not val_str.startswith('gAAAAA'):
        return val_str

    f = get_fernet()
    try:
        return f.decrypt(val_str.encode('utf-8')).decode('utf-8')
    except InvalidToken:
        return val_str


def hash_blind_index(value: str | None) -> str | None:
    """Return deterministic HMAC-SHA256 hash for exact-match database queries."""
    if value is None or value == '':
        return value
    secret = get_fernet_key()
    return hashlib.hmac.new(secret, value.strip().encode('utf-8'), hashlib.sha256).hexdigest()
