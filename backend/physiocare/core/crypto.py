import base64
import hashlib
import hmac
import os

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

_FERNET_INSTANCE: Fernet | None = None


def get_fernet_key() -> bytes:
    """Pobiera skonfigurowany klucz FIELD_ENCRYPTION_KEY lub generuje stabilny klucz na podstawie SECRET_KEY.

    Returns:
        bytes: Bajty klucza zakodowane w formacie base64.
    """
    key_str = os.environ.get('FIELD_ENCRYPTION_KEY', '').strip()
    if key_str:
        return key_str.encode('utf-8')

    secret = settings.SECRET_KEY if hasattr(settings, 'SECRET_KEY') else 'physiocare-default-encryption-secret-key-2026'
    derived = hashlib.sha256(secret.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(derived)


def get_fernet() -> Fernet:
    """Zwraca jedinstancjonowy (singleton) obiekt szyfrujący Fernet.

    Returns:
        Fernet: Instancja szyfratora Fernet.
    """
    global _FERNET_INSTANCE
    if _FERNET_INSTANCE is None:
        _FERNET_INSTANCE = Fernet(get_fernet_key())
    return _FERNET_INSTANCE


def reset_fernet_cache() -> None:
    """Czyści zbuforowaną instancję Fernet (przydatne przy testach i zmianie kluczy)."""
    global _FERNET_INSTANCE
    _FERNET_INSTANCE = None


def encrypt_value(value: str | None) -> str | None:
    """Szyfruje ciąg tekstowy do postaci ciągu zakodowanego Fernet (gAAAAA...).

    Args:
        value (str | None): Wartość tekstowa do zaszyfrowania.

    Returns:
        str | None: Zaszyfrowany tekst lub wartość oryginalna, jeśli podano None/pusty ciąg.

    Raises:
        TypeError: Gdy podana wartość nie jest typu str lub None.
    """
    if value is not None and not isinstance(value, str):
        raise TypeError("Argument 'value' musi być typu str lub None.")

    if value is None or value == '':
        return value

    if value.startswith('gAAAAA'):
        return value

    cipher = get_fernet()
    return cipher.encrypt(value.encode('utf-8')).decode('utf-8')


def decrypt_value(value: str | None) -> str | None:
    """Odszyfrowuje ciąg tekstowy zakodowany szyfrem Fernet do postaci tekstowej.

    Args:
        value (str | None): Zaszyfrowany ciąg tekstowy.

    Returns:
        str | None: Odszyfrowana wartość tekstowa lub oryginalny tekst przy błędzie/braku szyfrowania.

    Raises:
        TypeError: Gdy podana wartość nie jest typu str lub None.
    """
    if value is not None and not isinstance(value, str):
        raise TypeError("Argument 'value' musi być typu str lub None.")

    if value is None or value == '':
        return value

    if not value.startswith('gAAAAA'):
        return value

    cipher = get_fernet()
    try:
        return cipher.decrypt(value.encode('utf-8')).decode('utf-8')
    except InvalidToken:
        return value


def hash_blind_index(value: str | None) -> str | None:
    """Tworzy deterministyczny hash HMAC-SHA256 dla dokonywania dokładnych zapytani w bazie danych.

    Args:
        value (str | None): Wartość do zahashowania.

    Returns:
        str | None: Szesnastkowy ciąg reprezentujący hash HMAC.

    Raises:
        TypeError: Gdy podana wartość nie jest typu str lub None.
    """
    if value is not None and not isinstance(value, str):
        raise TypeError("Argument 'value' musi być typu str lub None.")

    if value is None or value == '':
        return value

    secret = get_fernet_key()
    return hmac.new(secret, value.strip().encode('utf-8'), hashlib.sha256).hexdigest()



