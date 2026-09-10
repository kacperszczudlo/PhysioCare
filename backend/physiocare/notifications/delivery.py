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

logger = logging.getLogger('physiocare.notifications')


def is_pref_enabled(user, pref_key: str) -> bool:
    ensure_default_preferences(user)
    pref = NotificationPreference.objects.filter(user=user, pref_key=pref_key).first()
    return bool(pref and pref.enabled)


def already_delivered(user, dedupe_key: str) -> bool:
    if not dedupe_key:
        return False
    return NotificationDelivery.objects.filter(user=user, dedupe_key=dedupe_key).exists()


def schedule_notify(user, pref_key: str, title: str, body: str, *, data=None, dedupe_key=''):
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
        logger.exception('Notification dispatch failed for user_id=%s', user.pk)


def notify_user(user, pref_key: str, title: str, body: str, *, data=None, dedupe_key=''):
    data = data or {}
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
            data=data,
            dedupe_key=dedupe_key,
        )
        return

    tokens = list(
        DeviceToken.objects.filter(user=user, is_active=True).values_list(
            'expo_push_token',
            flat=True,
        )
    )
    if tokens:
        _send_push(user, pref_key, title, body, data=data, dedupe_key=dedupe_key, tokens=tokens)
        return
    _send_email(user, pref_key, title, body, data=data, dedupe_key=dedupe_key)


def _send_push(user, pref_key, title, body, *, data, dedupe_key, tokens):
    messages = [
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
        tickets = send_expo_push(messages)
    except ExpoPushError as exc:
        logger.exception('Expo push failed for user_id=%s', user.pk)
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

    stale = []
    any_ok = False
    errors = []
    for token, ticket in zip(tokens, tickets, strict=False):
        status = (ticket or {}).get('status')
        if status == 'ok':
            any_ok = True
            continue
        details = (ticket or {}).get('details') or {}
        error_code = details.get('error') or (ticket or {}).get('message') or 'error'
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


def _send_email(user, pref_key, title, body, *, data, dedupe_key):
    email = getattr(user, 'email', '') or ''
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

    message = body
    try:
        send_mail(
            subject=f'PhysioCare - {title}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except (OSError, SMTPException) as exc:
        logger.exception('Notification e-mail failed for user_id=%s', user.pk)
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
