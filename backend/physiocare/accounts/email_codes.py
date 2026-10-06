from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .mail import send_templated_mail
from .models import EmailCode, EmailCodePurpose, PasswordResetToken


def hash_email_code(raw_code: str) -> str:
    """Tworzy hash SHA256 cyfrowego kodu e-mail.

    Args:
        raw_code (str): Niezaszyfrowany kod cyfrowy.

    Returns:
        str: Szesnastkowy ciąg reprezentujący hash.

    Raises:
        TypeError: Gdy raw_code nie jest typu str.
    """
    if not isinstance(raw_code, str):
        raise TypeError("Argument 'raw_code' musi być typu str.")
    return hashlib.sha256(raw_code.encode()).hexdigest()


def hash_password_reset_token(raw_token: str) -> str:
    """Tworzy hash SHA256 bezpiecznego tokenu URL do resetu hasła.

    Args:
        raw_token (str): Surowy ciąg tokena URL.

    Returns:
        str: Szesnastkowy ciąg reprezentujący hash.

    Raises:
        TypeError: Gdy raw_token nie jest typu str.
    """
    if not isinstance(raw_token, str):
        raise TypeError("Argument 'raw_token' musi być typu str.")
    return hashlib.sha256(raw_token.encode()).hexdigest()


DEFAULT_EMAIL_CODE_DIGITS: int = 6
DEFAULT_RESET_TTL_SECONDS: int = 900
MIN_RESET_TTL_SECONDS: int = 60
DEFAULT_EMAIL_CODE_MAX_ATTEMPTS: int = 5
RESET_TOKEN_ENTROPY_BYTES: int = 32
SECONDS_PER_MINUTE: int = 60


def generate_numeric_code(*, digits: int = DEFAULT_EMAIL_CODE_DIGITS) -> str:
    """Generuje losowy kod cyfrowy o wyznaczonej długości.

    Args:
        digits (int): Liczba cyfr kodu.

    Returns:
        str: Wygenerowany ciąg cyfr.

    Raises:
        TypeError: Gdy digits nie jest typu int.
    """
    if not isinstance(digits, int):
        raise TypeError("Argument 'digits' musi być typu int.")

    upper = 10**digits
    return f'{secrets.randbelow(upper):0{digits}d}'


def issue_email_code(*, user: object, purpose: str) -> str:
    """Unieważnia poprzednie aktywne kody użytkownika i generuje nowy kod cyfrowy.

    Args:
        user (object): Obiekt użytkownika Django.
        purpose (str): Cel wygenerowania kodu (np. weryfikacja e-mail, reset hasła).

    Returns:
        str: Wygenerowany niezaszyfrowany kod cyfrowy.

    Raises:
        TypeError: Gdy user jest None lub purpose nie jest typu str.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")
    if not isinstance(purpose, str):
        raise TypeError("Argument 'purpose' musi być typu str.")

    EmailCode.objects.filter(
        user=user,
        purpose=purpose,
        used_at__isnull=True,
    ).update(used_at=timezone.now())

    raw = generate_numeric_code()
    reset_timeout = settings.PASSWORD_RESET_TIMEOUT if hasattr(settings, 'PASSWORD_RESET_TIMEOUT') else DEFAULT_RESET_TTL_SECONDS
    ttl = max(
        MIN_RESET_TTL_SECONDS,
        int(reset_timeout),
    )
    EmailCode.objects.create(
        user=user,
        purpose=purpose,
        code_hash=hash_email_code(raw),
        expires_at=timezone.now() + timedelta(seconds=ttl),
    )
    return raw


def send_verify_email_code(*, user: object) -> bool:
    """Wysyła wiadomość e-mail z kodem weryfikacji adresu e-mail.

    Args:
        user (object): Obiekt użytkownika.

    Returns:
        bool: True jeśli wysyłka się powiodła, False w przeciwnym razie.

    Raises:
        TypeError: Gdy user jest None.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")

    raw = issue_email_code(user=user, purpose=EmailCodePurpose.VERIFY_EMAIL)
    reset_timeout = settings.PASSWORD_RESET_TIMEOUT if hasattr(settings, 'PASSWORD_RESET_TIMEOUT') else DEFAULT_RESET_TTL_SECONDS
    validity_minutes = max(
        1,
        int(reset_timeout) // SECONDS_PER_MINUTE,
    )
    user_email = user.email if hasattr(user, 'email') else ''
    first_name = user.first_name if hasattr(user, 'first_name') else ''

    return send_templated_mail(
        subject='PhysioCare - potwierdź adres e-mail',
        to=[user_email],
        template_basename='accounts/email/email_verify',
        context={
            'code': raw,
            'validity_minutes': validity_minutes,
            'first_name': first_name,
        },
    )


def send_password_reset_code(*, user: object) -> bool:
    """Wysyła e-mail z kodem do zresetowania hasła.

    Args:
        user (object): Obiekt użytkownika.

    Returns:
        bool: True jeśli wiadomość została pomyślnie nadana, False w przeciwnym wypadku.

    Raises:
        TypeError: Gdy user jest None.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")

    raw = issue_email_code(user=user, purpose=EmailCodePurpose.PASSWORD_RESET)
    reset_timeout = settings.PASSWORD_RESET_TIMEOUT if hasattr(settings, 'PASSWORD_RESET_TIMEOUT') else DEFAULT_RESET_TTL_SECONDS
    validity_minutes = max(
        1,
        int(reset_timeout) // SECONDS_PER_MINUTE,
    )
    user_email = user.email if hasattr(user, 'email') else ''
    first_name = user.first_name if hasattr(user, 'first_name') else ''

    return send_templated_mail(
        subject='PhysioCare - kod resetu hasła',
        to=[user_email],
        template_basename='accounts/email/password_reset',
        context={
            'code': raw,
            'validity_minutes': validity_minutes,
            'first_name': first_name,
        },
    )


def send_mfa_setup_code(*, user: object) -> bool:
    """Wysyła jednorazowy kod e-mail przed pierwszą konfiguracją MFA."""
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")

    raw = issue_email_code(user=user, purpose=EmailCodePurpose.MFA_SETUP)
    reset_timeout = settings.PASSWORD_RESET_TIMEOUT if hasattr(settings, 'PASSWORD_RESET_TIMEOUT') else DEFAULT_RESET_TTL_SECONDS
    validity_minutes = max(1, int(reset_timeout) // SECONDS_PER_MINUTE)
    user_email = user.email if hasattr(user, 'email') else ''
    first_name = user.first_name if hasattr(user, 'first_name') else ''

    return send_templated_mail(
        subject='PhysioCare - potwierdź konfigurację MFA',
        to=[user_email],
        template_basename='accounts/email/mfa_setup',
        context={
            'code': raw,
            'validity_minutes': validity_minutes,
            'first_name': first_name,
        },
    )


class EmailCodeError(Exception):
    """Wyjątek zgłaszany w przypadku błędów weryfikacji lub wygaśnięcia kodu e-mail."""

    def __init__(self, code: str, message: str) -> None:
        """Inicjalizuje obiekt błędu.

        Args:
            code (str): Kod błędu (np. AUTH_028).
            message (str): Treść komunikatu.

        Raises:
            TypeError: Gdy code lub message nie są typu str.
        """
        if not isinstance(code, str):
            raise TypeError("Argument 'code' musi być typu str.")
        if not isinstance(message, str):
            raise TypeError("Argument 'message' musi być typu str.")

        super().__init__(message)
        self.code = code
        self.message = message


def consume_email_code(*, user: object, purpose: str, raw_code: str) -> EmailCode:
    """Weryfikuje i oznacza kod jako użyty.

    Args:
        user (object): Obiekt użytkownika.
        purpose (str): Cel kodu.
        raw_code (str): Wprowadzony kod cyfrowy.

    Returns:
        EmailCode: Zaktualizowany rekord kodu e-mail.

    Raises:
        TypeError: Gdy user jest None, purpose lub raw_code nie są typu str.
        EmailCodeError: Gdy kod jest błędny, wygasł lub przekroczono limit prób.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")
    if not isinstance(purpose, str):
        raise TypeError("Argument 'purpose' musi być typu str.")
    if not isinstance(raw_code, str):
        raise TypeError("Argument 'raw_code' musi być typu str.")

    cleaned = raw_code.strip()
    if not cleaned.isdigit() or len(cleaned) != DEFAULT_EMAIL_CODE_DIGITS:
        raise EmailCodeError('AUTH_028', f'Kod musi składać się z {DEFAULT_EMAIL_CODE_DIGITS} cyfr.')

    max_attempts_setting = settings.EMAIL_CODE_MAX_ATTEMPTS if hasattr(settings, 'EMAIL_CODE_MAX_ATTEMPTS') else DEFAULT_EMAIL_CODE_MAX_ATTEMPTS
    max_attempts = max(1, int(max_attempts_setting))
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


def issue_password_reset_token(*, user: object) -> str:
    """Unieważnia poprzednie tokeny i tworzy nowy token resetu hasła.

    Args:
        user (object): Użytkownik proszący o reset hasła.

    Returns:
        str: Nowo wygenerowany surowy token URL.

    Raises:
        TypeError: Gdy user jest None.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")

    PasswordResetToken.objects.filter(
        user=user,
        used_at__isnull=True,
    ).update(used_at=timezone.now())

    raw = secrets.token_urlsafe(RESET_TOKEN_ENTROPY_BYTES)
    reset_timeout = settings.PASSWORD_RESET_TIMEOUT if hasattr(settings, 'PASSWORD_RESET_TIMEOUT') else DEFAULT_RESET_TTL_SECONDS
    ttl = max(
        MIN_RESET_TTL_SECONDS,
        int(reset_timeout),
    )
    PasswordResetToken.objects.create(
        user=user,
        token_hash=hash_password_reset_token(raw),
        expires_at=timezone.now() + timedelta(seconds=ttl),
    )
    return raw


def lookup_password_reset_token(*, raw_token: str) -> PasswordResetToken | None:
    """Wyszukuje aktywny, niewygasły token resetu hasła.

    Args:
        raw_token (str): Surowy token URL.

    Returns:
        PasswordResetToken | None: Obiekt tokenu lub None.

    Raises:
        TypeError: Gdy raw_token nie jest typu str.
    """
    if not isinstance(raw_token, str):
        raise TypeError("Argument 'raw_token' musi być typu str.")

    cleaned = raw_token.strip()
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


def consume_password_reset_token(*, raw_token: str) -> object:
    """Waliduje i oznacza token resetu hasła jako wykorzystany.

    Args:
        raw_token (str): Surowy token z adresu URL.

    Returns:
        object: Obiekt użytkownika powiązanego z tokenem.

    Raises:
        TypeError: Gdy raw_token nie jest typu str.
        EmailCodeError: Gdy token wygasł lub nie istnieje.
    """
    if not isinstance(raw_token, str):
        raise TypeError("Argument 'raw_token' musi być typu str.")

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

