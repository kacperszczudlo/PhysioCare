import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import send_mail

from notifications.defaults import ensure_default_preferences
from notifications.expo import ExpoPushError, send_expo_push
from notifications.models import (
    DeliveryChannel,
    DeliveryStatus,
    DeviceToken,
    NotificationDelivery,
    NotificationPreference,
)

logger: logging.Logger = logging.getLogger('physiocare.notifications')


def is_pref_enabled(user: object, pref_key: str) -> bool:
    """Sprawdza, czy dany typ powiadomienia jest włączony w preferencjach użytkownika.

    Args:
        user (object): Obiekt użytkownika Django.
        pref_key (str): Klucz preferencji powiadomienia.

    Returns:
        bool: True jeśli powiadomienie jest włączone, False w przeciwnym razie.

    Raises:
        TypeError: Gdy parametr pref_key nie jest napisem lub user jest None.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")
    if not isinstance(pref_key, str):
        raise TypeError('Klucz preferencji (pref_key) musi być ciągiem znaków.')

    ensure_default_preferences(user)
    pref: NotificationPreference | None = NotificationPreference.objects.filter(user=user, pref_key=pref_key).first()
    return bool(pref and pref.enabled)


def already_delivered(user: object, dedupe_key: str) -> bool:
    """Sprawdza, czy powiadomienie o podanym kluczu deduplikacji zostało już doręczone.

    Args:
        user (object): Obiekt użytkownika Django.
        dedupe_key (str): Unikalny klucz deduplikacji.

    Returns:
        bool: True jeśli powiadomienie już istnieje, False w przeciwnym wypadku.

    Raises:
        TypeError: Gdy dedupe_key nie jest typu str lub user jest None.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")
    if not isinstance(dedupe_key, str):
        raise TypeError("Argument 'dedupe_key' musi być typu str.")

    if not dedupe_key:
        return False
    return NotificationDelivery.objects.filter(user=user, dedupe_key=dedupe_key).exists()


def schedule_notify(
    user: object,
    pref_key: str,
    title: str,
    body: str,
    *,
    data: dict[str, object] | None = None,
    dedupe_key: str = '',
) -> None:
    """Bezpiecznie szereguje wysyłkę powiadomienia do użytkownika przechwytując ewentualne wyjątki.

    Args:
        user (object): Adresat powiadomienia.
        pref_key (str): Klucz kategorii powiadomienia.
        title (str): Tytuł powiadomienia.
        body (str): Treść wiadomości.
        data (dict[str, object] | None): Dodatkowe metadane w formacie słownika.
        dedupe_key (str): Klucz deduplikacji.

    Raises:
        TypeError: Gdy parametry tekstowe nie są typu str lub user jest None.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")
    if not isinstance(pref_key, str) or not isinstance(title, str) or not isinstance(body, str):
        raise TypeError('Parametry pref_key, title oraz body muszą być ciągami znaków.')

    try:
        notify_user(
            user,
            pref_key,
            title,
            body,
            data=dict(data or {}),
            dedupe_key=dedupe_key,
        )
    except Exception:
        user_pk: object = getattr(user, 'pk', 'unknown') if hasattr(user, 'pk') else 'unknown'
        user_id_str: str = str(user.pk) if hasattr(user, 'pk') else 'unknown'
        logger.exception('Notification dispatch failed for user_id=%s', user_id_str)


def notify_user(
    user: object,
    pref_key: str,
    title: str,
    body: str,
    *,
    data: dict[str, object] | None = None,
    dedupe_key: str = '',
) -> None:
    """Wysyła powiadomienie do użytkownika przy użyciu odpowiedniego kanału (Push/Email).

    Args:
        user (object): Obiekt użytkownika Django.
        pref_key (str): Klucz typu powiadomienia.
        title (str): Tytuł powiadomienia.
        body (str): Treść wiadomości.
        data (dict[str, object] | None): Dane dodatkowe payloadu.
        dedupe_key (str): Klucz deduplikacji zapobiegający powieleniom.

    Raises:
        TypeError: Gdy parametry tekstowe nie są typu str lub user jest None.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")
    if not isinstance(pref_key, str) or not isinstance(title, str) or not isinstance(body, str):
        raise TypeError('Parametry pref_key, title oraz body muszą być ciągami znaków.')

    payload_data: dict[str, object] = data or {}
    if not isinstance(payload_data, dict):
        payload_data = {}

    if already_delivered(user, dedupe_key):
        return

    if not is_pref_enabled(user, pref_key):
        NotificationDelivery.objects.create(
            user=user,
            pref_key=pref_key,
            channel=DeliveryChannel.NONE,
            status=DeliveryStatus.SKIPPED,
            title=title,
            body=body,
            data=payload_data,
            dedupe_key=dedupe_key,
        )
        return

    tokens: list[str] = list(
        DeviceToken.objects.filter(user=user, is_active=True).values_list(
            'expo_push_token',
            flat=True,
        )
    )
    if tokens:
        _send_push(user, pref_key, title, body, data=payload_data, dedupe_key=dedupe_key, tokens=tokens)
        return
    _send_email(user, pref_key, title, body, data=payload_data, dedupe_key=dedupe_key)


def _send_push(
    user: object,
    pref_key: str,
    title: str,
    body: str,
    *,
    data: dict[str, object],
    dedupe_key: str,
    tokens: list[str],
) -> None:
    """Wewnętrzna funkcja wysyłająca powiadomienie Push przez sieć Expo.

    Args:
        user (object): Obiekt użytkownika.
        pref_key (str): Klucz kategorii powiadomień.
        title (str): Tytuł.
        body (str): Treść.
        data (dict[str, object]): Dodatkowe dane.
        dedupe_key (str): Klucz deduplikacji.
        tokens (list[str]): Lista aktywnych tokenów urządzeń.

    Raises:
        TypeError: Gdy tokens nie jest listą lub user jest None.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")
    if not isinstance(tokens, list):
        raise TypeError("Argument 'tokens' musi być listą list[str].")

    messages: list[dict[str, object]] = [
        {
            'to': token,
            'title': title,
            'body': body,
            'sound': 'default',
            'data': data,
        }
        for token in tokens
    ]
    try:
        tickets: list[dict[str, object]] = send_expo_push(messages)
    except ExpoPushError as exc:
        user_id_str: str = str(user.pk) if hasattr(user, 'pk') else 'unknown'
        logger.exception('Expo push failed for user_id=%s', user_id_str)
        NotificationDelivery.objects.create(
            user=user,
            pref_key=pref_key,
            channel=DeliveryChannel.PUSH,
            status=DeliveryStatus.FAILED,
            title=title,
            body=body,
            data=data,
            dedupe_key=dedupe_key,
            error_message=str(exc)[:300],
        )
        _send_email(user, pref_key, title, body, data=data, dedupe_key='')
        return

    stale: list[str] = []
    any_ok: bool = False
    errors: list[str] = []
    for token, ticket in zip(tokens, tickets, strict=False):
        t_status: object = (ticket or {}).get('status')
        if t_status == 'ok':
            any_ok = True
            continue
        details: dict[str, object] = (ticket or {}).get('details') or {}  # type: ignore[assignment]
        error_code: object = details.get('error') or (ticket or {}).get('message') or 'error'
        errors.append(str(error_code))
        if error_code == 'DeviceNotRegistered':
            stale.append(token)

    if stale:
        DeviceToken.objects.filter(expo_push_token__in=stale).update(is_active=False)

    NotificationDelivery.objects.create(
        user=user,
        pref_key=pref_key,
        channel=DeliveryChannel.PUSH,
        status=DeliveryStatus.SENT if any_ok else DeliveryStatus.FAILED,
        title=title,
        body=body,
        data=data,
        dedupe_key=dedupe_key,
        error_message=', '.join(errors)[:300],
    )
    if not any_ok:
        _send_email(user, pref_key, title, body, data=data, dedupe_key='')


def _send_email(
    user: object,
    pref_key: str,
    title: str,
    body: str,
    *,
    data: dict[str, object],
    dedupe_key: str,
) -> None:
    """Wewnętrzna funkcja wysyłająca powiadomienie e-mail w przypadku braku tokenów Push lub ich niepowodzenia.

    Args:
        user (object): Obiekt użytkownika.
        pref_key (str): Klucz kategorii powiadomienia.
        title (str): Tytuł e-maila.
        body (str): Treść e-maila.
        data (dict[str, object]): Dodatkowe dane.
        dedupe_key (str): Klucz deduplikacji.

    Raises:
        TypeError: Gdy user jest None.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")

    email: str = user.email if hasattr(user, 'email') and user.email else ''
    if not email:
        NotificationDelivery.objects.create(
            user=user,
            pref_key=pref_key,
            channel=DeliveryChannel.EMAIL,
            status=DeliveryStatus.FAILED,
            title=title,
            body=body,
            data=data,
            dedupe_key=dedupe_key,
            error_message='Brak adresu e-mail.',
        )
        return

    message: str = body
    try:
        send_mail(
            subject=f'PhysioCare - {title}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except (OSError, SMTPException) as exc:
        user_id_str: str = str(user.pk) if hasattr(user, 'pk') else 'unknown'
        logger.exception('Notification e-mail failed for user_id=%s', user_id_str)
        NotificationDelivery.objects.create(
            user=user,
            pref_key=pref_key,
            channel=DeliveryChannel.EMAIL,
            status=DeliveryStatus.FAILED,
            title=title,
            body=body,
            data=data,
            dedupe_key=dedupe_key,
            error_message=str(exc)[:300],
        )
        return

    NotificationDelivery.objects.create(
        user=user,
        pref_key=pref_key,
        channel=DeliveryChannel.EMAIL,
        status=DeliveryStatus.SENT,
        title=title,
        body=body,
        data=data,
        dedupe_key=dedupe_key,
    )
