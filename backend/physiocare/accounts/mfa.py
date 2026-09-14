import hashlib
import io
import logging
import secrets
import string

import pyotp
import qrcode
import qrcode.image.svg
from django.contrib.auth import get_user_model
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner

User = get_user_model()
logger = logging.getLogger('physiocare.auth')

MFA_PREAUTH_SALT = 'physiocare.2fa.preauth'
MFA_PREAUTH_MAX_AGE = 300  # 5 minutes

TOTP_CODE_LENGTH = 6
TOTP_VALID_WINDOW = 1
DEFAULT_BACKUP_CODES_COUNT = 8
BACKUP_CODE_CHAR_LENGTH = 8
BACKUP_CODE_FORMAT_SPLIT = 4


def generate_totp_secret() -> str:
    """Generate a new 32-character Base32 secret for TOTP."""
    return pyotp.random_base32()


def get_totp_uri(user, secret: str) -> str:
    """Return provisioning URI for TOTP authenticator apps."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=user.email, issuer_name='PhysioCare')


def generate_qr_code_svg(otpauth_url: str) -> str:
    """Generate SVG XML string of QR code encoding otpauth URL."""
    factory = qrcode.image.svg.SvgPathImage
    img = qrcode.make(otpauth_url, image_factory=factory)
    stream = io.BytesIO()
    img.save(stream)
    return stream.getvalue().decode('utf-8')


def verify_totp_code(secret: str, code: str) -> bool:
    """Verify a TOTP code against the secret key (tolerance window = 1)."""
    if not secret or not code:
        return False
    clean_code = str(code).strip().replace(' ', '').replace('-', '')
    if not clean_code.isdigit() or len(clean_code) != TOTP_CODE_LENGTH:
        return False
    totp = pyotp.TOTP(secret)
    return bool(totp.verify(clean_code, valid_window=TOTP_VALID_WINDOW))


def generate_backup_codes(count: int = DEFAULT_BACKUP_CODES_COUNT) -> tuple[list[str], list[str]]:
    """Generate raw single-use backup codes and their SHA-256 hashes."""
    alphabet = string.ascii_uppercase + string.digits
    # Exclude ambiguous characters like O, 0, I, 1 for usability
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


def verify_and_consume_backup_code(user_mfa, code: str) -> bool:
    """Verify and consume a backup recovery code if valid."""
    if not user_mfa or not user_mfa.backup_codes or not code:
        return False

    clean_code = str(code).strip().replace('-', '').replace(' ', '').upper()
    code_hash = hashlib.sha256(clean_code.encode('utf-8')).hexdigest()

    if code_hash in user_mfa.backup_codes:
        updated_codes = [h for h in user_mfa.backup_codes if h != code_hash]
        user_mfa.backup_codes = updated_codes
        user_mfa.save(update_fields=['backup_codes', 'updated_at'])
        logger.info('Backup code consumed for user=%s', user_mfa.user.email)
        return True

    return False


def issue_mfa_preauth_token(user) -> str:
    """Issue short-lived signed preauth token for step-2 2FA login."""
    signer = TimestampSigner(salt=MFA_PREAUTH_SALT)
    return signer.sign(str(user.id))


def verify_mfa_preauth_token(token: str, max_age: int = MFA_PREAUTH_MAX_AGE):
    """Verify preauth token and return CustomUser or None."""
    if not token:
        return None
    signer = TimestampSigner(salt=MFA_PREAUTH_SALT)
    try:
        user_id_str = signer.unsign(token, max_age=max_age)
        return User.objects.filter(id=user_id_str, is_active=True).first()
    except (SignatureExpired, BadSignature, ValueError):
        return None
