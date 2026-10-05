import hashlib
import io
import hashlib
import logging
import secrets
import secrets
import string

import pyotp
import qrcode
import qrcode.image.svg
from django.contrib.auth import get_user_model
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner

from core.logging_formatters import mask_email_for_logging

User: type[object] = get_user_model()
logger: logging.Logger = logging.getLogger('physiocare.auth')

MFA_PREAUTH_SALT: str = 'physiocare.2fa.preauth'
MFA_PREAUTH_MAX_AGE: int = 300
MFA_SETUP_SALT: str = 'physiocare.2fa.setup'
MFA_SETUP_MAX_AGE: int = 600

TOTP_CODE_LENGTH: int = 6
TOTP_VALID_WINDOW: int = 1
DEFAULT_BACKUP_CODES_COUNT: int = 8
BACKUP_CODE_CHAR_LENGTH: int = 8
BACKUP_CODE_FORMAT_SPLIT: int = 4


def generate_totp_secret() -> str:
    """Generuje nowy 32-znakowy klucz sekretny Base32 dla TOTP.

    Returns:
        str: Wygenerowany sekret Base32.
    """
    return pyotp.random_base32()


def get_totp_uri(user: object, secret: str) -> str:
    """Zwraca URI konfiguracyjne dla aplikacji autoryzacyjnych TOTP.

    Args:
        user (object): Obiekt użytkownika posiadający atrybut email.
        secret (str): Sekretny klucz TOTP.

    Returns:
        str: Adres URL w formacie otpauth://.

    Raises:
        TypeError: Gdy user jest None lub secret nie jest typu str.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")
    if not isinstance(secret, str):
        raise TypeError("Argument 'secret' musi być typu str.")

    user_email = user.email if hasattr(user, 'email') else ''
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=user_email, issuer_name='PhysioCare')


def generate_qr_code_svg(otpauth_url: str) -> str:
    """Generuje ciąg XML w formacie SVG przedstawiający kod QR.

    Args:
        otpauth_url (str): Adres URL w formacie otpauth://.

    Returns:
        str: Zawartość pliku SVG kodującego podany URL.

    Raises:
        TypeError: Gdy otpauth_url nie jest typu str.
    """
    if not isinstance(otpauth_url, str):
        raise TypeError("Argument 'otpauth_url' musi być typu str.")

    factory = qrcode.image.svg.SvgPathImage
    img = qrcode.make(otpauth_url, image_factory=factory)
    stream = io.BytesIO()
    img.save(stream)
    return stream.getvalue().decode('utf-8')


def verify_totp_code(secret: str, code: str) -> bool:
    """Weryfikuje podany kod TOTP względem klucza sekretnego.

    Args:
        secret (str): Sekretny klucz TOTP.
        code (str): Wprowadzony jednorazowy kod cyfrowy.

    Returns:
        bool: True jeśli kod jest prawidłowy, False w przeciwnym razie.

    Raises:
        TypeError: Gdy secret lub code nie są typu str.
    """
    if not isinstance(secret, str):
        raise TypeError("Argument 'secret' musi być typu str.")
    if not isinstance(code, str):
        raise TypeError("Argument 'code' musi być typu str.")

    if not secret or not code:
        return False
    clean_code = code.strip().replace(' ', '').replace('-', '')
    if not clean_code.isdigit() or len(clean_code) != TOTP_CODE_LENGTH:
        return False
    totp = pyotp.TOTP(secret)
    return bool(totp.verify(clean_code, valid_window=TOTP_VALID_WINDOW))


def generate_backup_codes(count: int = DEFAULT_BACKUP_CODES_COUNT) -> tuple[list[str], list[str]]:
    """Generuje jawnym tekstem kody zapasowe oraz ich skróty SHA-256.

    Args:
        count (int): Liczba kodów zapasowych do wygenerowania.

    Returns:
        tuple[list[str], list[str]]: Krotka zawierająca listę czytelnych kodów i listę ich skrótów SHA-256.

    Raises:
        TypeError: Gdy count nie jest typu int.
    """
    if not isinstance(count, int):
        raise TypeError("Argument 'count' musi być typu int.")

    alphabet = string.ascii_uppercase + string.digits
    clean_alphabet = ''.join(c for c in alphabet if c not in 'O0I1')
    raw_codes = []
    hashed_codes = []

    for _ in range(count):
        code = ''.join(secrets.choice(clean_alphabet) for _ in range(BACKUP_CODE_CHAR_LENGTH))
        code_formatted = f'{code[:BACKUP_CODE_FORMAT_SPLIT]}-{code[BACKUP_CODE_FORMAT_SPLIT:]}'
        raw_codes.append(code_formatted)
        code_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()
        hashed_codes.append(code_hash)

    return raw_codes, hashed_codes


def verify_and_consume_backup_code(user_mfa: object, code: str) -> bool:
    """Weryfikuje i zużywa kod zapasowy użytkownika jeśli jest prawidłowy.

    Args:
        user_mfa (object): Obiekt ustawień MFA użytkownika.
        code (str): Wprowadzony kod zapasowy.

    Returns:
        bool: True jeśli kod był prawidłowy i został zużyty, False w przeciwnym razie.

    Raises:
        TypeError: Gdy user_mfa jest None lub code nie jest typu str.
    """
    if user_mfa is None:
        raise TypeError("Argument 'user_mfa' nie może być None.")
    if not isinstance(code, str):
        raise TypeError("Argument 'code' musi być typu str.")

    if not hasattr(user_mfa, 'backup_codes') or not user_mfa.backup_codes or not code:
        return False

    clean_code = code.strip().replace('-', '').replace(' ', '').upper()
    code_hash = hashlib.sha256(clean_code.encode('utf-8')).hexdigest()

    backup_codes = user_mfa.backup_codes if hasattr(user_mfa, 'backup_codes') else []
    if code_hash in backup_codes:
        updated_codes = [h for h in backup_codes if h != code_hash]
        user_mfa.backup_codes = updated_codes
        if hasattr(user_mfa, 'save'):
            user_mfa.save(update_fields=['backup_codes', 'updated_at'])
        user_obj = user_mfa.user if hasattr(user_mfa, 'user') else None
        user_email = user_obj.email if user_obj and hasattr(user_obj, 'email') else 'unknown'
        logger.info(
            'Backup code consumed for user_id=%s email=%s',
            getattr(user_obj, 'id', None),
            mask_email_for_logging(user_email),
        )
        return True

    return False


def issue_mfa_preauth_token(user: object) -> str:
    """Generuje krótkotrwały podpisany token pre-autoryzacji dwuetapowej.

    Args:
        user (object): Instancja użytkownika.

    Returns:
        str: Podpisany token tekstowy.

    Raises:
        TypeError: Gdy user jest None.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")

    signer = TimestampSigner(salt=MFA_PREAUTH_SALT)
    user_id = user.id if hasattr(user, 'id') else user
    return signer.sign(str(user_id))


def verify_mfa_preauth_token(token: str, max_age: int = MFA_PREAUTH_MAX_AGE) -> object | None:
    """Weryfikuje token pre-autoryzacji i zwraca obiekt użytkownika.

    Args:
        token (str): Podpisany token.
        max_age (int): Maksymalny wiek tokenu w sekundach.

    Returns:
        object | None: Instancja użytkownika lub None jeśli token jest nieprawidłowy/wygasł.

    Raises:
        TypeError: Gdy token nie jest typu str lub max_age nie jest typu int.
    """
    if not isinstance(token, str):
        raise TypeError("Argument 'token' musi być typu str.")
    if not isinstance(max_age, int):
        raise TypeError("Argument 'max_age' musi być typu int.")

    if not token:
        return None
    signer = TimestampSigner(salt=MFA_PREAUTH_SALT)
    try:
        user_id_str = signer.unsign(token, max_age=max_age)
        return User.objects.filter(id=user_id_str, is_active=True).first()
    except (SignatureExpired, BadSignature, ValueError):
        return None


def issue_mfa_setup_token(user: object, email_verified: bool = False) -> str:
    """Generuje krótkotrwały token ograniczony do pierwszej konfiguracji MFA."""
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")

    signer = TimestampSigner(salt=MFA_SETUP_SALT)
    user_id = user.id if hasattr(user, 'id') else user
    flag = 'ev' if email_verified else 'p'
    return signer.sign(f'{user_id}:{secrets.token_urlsafe(32)}:{flag}')


def verify_mfa_setup_token(token: str, max_age: int = MFA_SETUP_MAX_AGE) -> object | None:
    """Weryfikuje token konfiguracji MFA i zwraca aktywnego użytkownika."""
    if not isinstance(token, str):
        raise TypeError("Argument 'token' musi być typu str.")
    if not isinstance(max_age, int):
        raise TypeError("Argument 'max_age' musi być typu int.")

    if not token:
        return None
    signer = TimestampSigner(salt=MFA_SETUP_SALT)
    try:
        signed_value = signer.unsign(token, max_age=max_age)
        parts = signed_value.split(':')
        if len(parts) < 2:
            return None
        user_id_str = parts[0]
        if not user_id_str:
            return None
        return User.objects.filter(id=user_id_str, is_active=True).first()
    except (SignatureExpired, BadSignature, ValueError):
        return None


def is_mfa_setup_token_email_verified(token: str, max_age: int = MFA_SETUP_MAX_AGE) -> bool:
    """Sprawdza, czy token konfiguracji MFA został wystawiony po zweryfikowaniu e-maila."""
    if not isinstance(token, str) or not isinstance(max_age, int) or not token:
        return False
    signer = TimestampSigner(salt=MFA_SETUP_SALT)
    try:
        signed_value = signer.unsign(token, max_age=max_age)
        parts = signed_value.split(':')
        return len(parts) >= 3 and parts[2] == 'ev'
    except (SignatureExpired, BadSignature, ValueError):
        return False


def hash_mfa_setup_token(token: str) -> str:
    """Zwraca jednokierunkowy skrót tokenu konfiguracji MFA do zapisania w bazie."""
    if not isinstance(token, str):
        raise TypeError("Argument 'token' musi być typu str.")
    return hashlib.sha256(token.encode('utf-8')).hexdigest()
