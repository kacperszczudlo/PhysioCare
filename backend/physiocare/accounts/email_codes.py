"""Issue and verify 6-digit e-mail codes (verify + password reset)."""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .mail import send_templated_mail
from .models import EmailCode, EmailCodePurpose, PasswordResetToken


def hash_email_code(raw_code: str) -> str:
    return hashlib.sha256(raw_code.encode()).hexdigest()


def hash_password_reset_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


DEFAULT_EMAIL_CODE_DIGITS = 6
DEFAULT_RESET_TTL_SECONDS = 900
MIN_RESET_TTL_SECONDS = 60
DEFAULT_EMAIL_CODE_MAX_ATTEMPTS = 5
RESET_TOKEN_ENTROPY_BYTES = 32
SECONDS_PER_MINUTE = 60


def generate_numeric_code(*, digits: int = DEFAULT_EMAIL_CODE_DIGITS) -> str:
    upper = 10**digits
    return f'{secrets.randbelow(upper):0{digits}d}'


def issue_email_code(*, user, purpose: str) -> str:
    """Invalidate previous active codes, create a new one, return raw code."""
    EmailCode.objects.filter(
        user=user,
        purpose=purpose,
        used_at__isnull=True,
    ).update(used_at=timezone.now())

    raw = generate_numeric_code()
    ttl = max(
        MIN_RESET_TTL_SECONDS,
        int(getattr(settings, 'PASSWORD_RESET_TIMEOUT', DEFAULT_RESET_TTL_SECONDS)),
    )
    EmailCode.objects.create(
        user=user,
        purpose=purpose,
        code_hash=hash_email_code(raw),
        expires_at=timezone.now() + timedelta(seconds=ttl),
    )
    return raw


def send_verify_email_code(*, user) -> bool:
    raw = issue_email_code(user=user, purpose=EmailCodePurpose.VERIFY_EMAIL)
    validity_minutes = max(
        1,
        int(getattr(settings, 'PASSWORD_RESET_TIMEOUT', DEFAULT_RESET_TTL_SECONDS)) // SECONDS_PER_MINUTE,
    )
    return send_templated_mail(
        subject='PhysioCare - potwierdź adres e-mail',
        to=[user.email],
        template_basename='accounts/email/email_verify',
        context={
            'code': raw,
            'validity_minutes': validity_minutes,
            'first_name': user.first_name,
        },
    )


def send_password_reset_code(*, user) -> bool:
    raw = issue_email_code(user=user, purpose=EmailCodePurpose.PASSWORD_RESET)
    validity_minutes = max(
        1,
        int(getattr(settings, 'PASSWORD_RESET_TIMEOUT', DEFAULT_RESET_TTL_SECONDS)) // SECONDS_PER_MINUTE,
    )
    return send_templated_mail(
        subject='PhysioCare - kod resetu hasła',
        to=[user.email],
        template_basename='accounts/email/password_reset',
        context={
            'code': raw,
            'validity_minutes': validity_minutes,
            'first_name': user.first_name,
        },
    )


class EmailCodeError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def consume_email_code(*, user, purpose: str, raw_code: str) -> EmailCode:
    """Validate and mark code used. Raises EmailCodeError on failure."""
    cleaned = (raw_code or '').strip()
    if not cleaned.isdigit() or len(cleaned) != DEFAULT_EMAIL_CODE_DIGITS:
        raise EmailCodeError('AUTH_028', f'Kod musi składać się z {DEFAULT_EMAIL_CODE_DIGITS} cyfr.')

    max_attempts = max(1, int(getattr(settings, 'EMAIL_CODE_MAX_ATTEMPTS', DEFAULT_EMAIL_CODE_MAX_ATTEMPTS)))
    record = (
        EmailCode.objects.filter(
            user=user,
            purpose=purpose,
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .order_by('-created_at')
        .first()
    )
    if record is None:
        raise EmailCodeError('AUTH_028', 'Kod jest nieprawidłowy lub wygasł.')

    if record.attempts >= max_attempts:
        record.used_at = timezone.now()
        record.save(update_fields=['used_at'])
        raise EmailCodeError(
            'AUTH_028',
            'Przekroczono limit prób. Poproś o nowy kod.',
        )

    if not secrets.compare_digest(record.code_hash, hash_email_code(cleaned)):
        record.attempts += 1
        record.save(update_fields=['attempts'])
        if record.attempts >= max_attempts:
            record.used_at = timezone.now()
            record.save(update_fields=['used_at'])
            raise EmailCodeError(
                'AUTH_028',
                'Przekroczono limit prób. Poproś o nowy kod.',
            )
        raise EmailCodeError('AUTH_028', 'Kod jest nieprawidłowy lub wygasł.')

    record.used_at = timezone.now()
    record.save(update_fields=['used_at'])
    EmailCode.objects.filter(
        user=user,
        purpose=purpose,
        used_at__isnull=True,
    ).exclude(id=record.id).update(used_at=timezone.now())
    return record


def issue_password_reset_token(*, user) -> str:
    """Invalidate previous unused tokens, create a new one, return raw token."""
    PasswordResetToken.objects.filter(
        user=user,
        used_at__isnull=True,
    ).update(used_at=timezone.now())

    raw = secrets.token_urlsafe(RESET_TOKEN_ENTROPY_BYTES)
    ttl = max(
        MIN_RESET_TTL_SECONDS,
        int(getattr(settings, 'PASSWORD_RESET_TIMEOUT', DEFAULT_RESET_TTL_SECONDS)),
    )
    PasswordResetToken.objects.create(
        user=user,
        token_hash=hash_password_reset_token(raw),
        expires_at=timezone.now() + timedelta(seconds=ttl),
    )
    return raw


def lookup_password_reset_token(*, raw_token: str):
    """Return unused, unexpired PasswordResetToken or None."""
    cleaned = (raw_token or '').strip()
    if not cleaned:
        return None
    return (
        PasswordResetToken.objects.select_related('user')
        .filter(
            token_hash=hash_password_reset_token(cleaned),
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .first()
    )


def consume_password_reset_token(*, raw_token: str):
    """Validate and mark reset token used. Returns user. Raises EmailCodeError."""
    record = lookup_password_reset_token(raw_token=raw_token)
    if record is None:
        raise EmailCodeError('AUTH_028', 'Sesja resetu wygasła. Poproś o nowy kod.')

    record.used_at = timezone.now()
    record.save(update_fields=['used_at'])
    PasswordResetToken.objects.filter(
        user=record.user,
        used_at__isnull=True,
    ).exclude(id=record.id).update(used_at=timezone.now())
    return record.user
