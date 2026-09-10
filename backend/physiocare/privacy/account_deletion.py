"""Account deletion: deactivate, anonymize PII, free e-mail for re-registration."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from notifications.models import DeviceToken

from .models import AccountDeletionRequest

User = get_user_model()


@transaction.atomic
def free_inactive_email_holder(email: str) -> bool:
    """If an inactive user still holds ``email``, anonymize them so it can be reused.

    Returns True when an inactive holder was freed.
    """
    normalized = User.objects.normalize_email(email)
    holder = (
        User.objects.filter(email__iexact=normalized, is_active=False)
        .select_for_update()
        .first()
    )
    if holder is None:
        return False
    anonymize_user_for_deletion(holder, reason='', source='re_registration')
    return True


@transaction.atomic
def submit_account_deletion(user, *, reason: str = '') -> AccountDeletionRequest:
    """Register deletion request, revoke sessions/tokens, and anonymize the user."""
    reason = (reason or '').strip()[:2000]
    original_email = user.email

    DeviceToken.objects.filter(user=user, is_active=True).update(
        is_active=False,
        updated_at=timezone.now(),
    )

    deletion, _created = AccountDeletionRequest.objects.get_or_create(user=user)
    if reason:
        deletion.reason = reason
    if original_email and not original_email.startswith('deleted-'):
        note = f'email_at_request={original_email}'
        if deletion.notes:
            if note not in deletion.notes:
                deletion.notes = f'{deletion.notes}\n{note}'
        else:
            deletion.notes = note
    deletion.save()

    anonymize_user_for_deletion(user, reason=reason, source='user_request')
    return deletion


def anonymize_user_for_deletion(
    user,
    *,
    reason: str = '',
    source: str = 'user_request',
) -> None:
    """Soft-delete: deactivate, scrub PII, free e-mail and Google subject."""
    if user.email.startswith('deleted-') and not user.is_active:
        return

    user.email = f'deleted-{user.pk}@deleted.invalid'
    user.first_name = 'Usunięte'
    user.last_name = 'Konto'
    user.google_sub = None
    user.email_verified_at = None
    user.is_active = False
    user.set_unusable_password()
    user.save(
        update_fields=[
            'email',
            'first_name',
            'last_name',
            'google_sub',
            'email_verified_at',
            'is_active',
            'password',
            'updated_at',
        ]
    )

    profile = getattr(user, 'patient_profile', None)
    if profile is not None:
        profile.pesel = None
        profile.phone = ''
        profile.avatar_url = ''
        profile.save(update_fields=['pesel', 'phone', 'avatar_url'])

    DeviceToken.objects.filter(user=user, is_active=True).update(
        is_active=False,
        updated_at=timezone.now(),
    )

    if source == 're_registration':
        AccountDeletionRequest.objects.get_or_create(
            user=user,
            defaults={
                'reason': reason or 'Zwolniono e-mail przy ponownej rejestracji.',
                'notes': 'anonymized_on_re_registration=1',
            },
        )
