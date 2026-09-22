from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from notifications.models import DeviceToken

from .models import AccountDeletionRequest

User = get_user_model()


@transaction.atomic
def free_inactive_email_holder(email: str) -> bool:
    """Anonimizuje nieaktywne konto posiadające dany e-mail, aby umożliwić ponowną rejestrację.

    Args:
        email (str): Adres e-mail do zwolnienia.

    Returns:
        bool: True jeśli znaleziono i zanonimizowano nieaktywnego użytkownika, False w przeciwnym razie.
    """
    if not isinstance(email, str):
        return False

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
def submit_account_deletion(user: object, *, reason: str = '') -> AccountDeletionRequest:
    """Rejestruje wniosek o usunięcie konta, unieważnia sesje i anonimizuje dane osobowe użytkownika.

    Args:
        user (object): Obiekt usuwanego użytkownika.
        reason (str): Opcjonalny powód usunięcia konta podany przez użytkownika.

    Returns:
        AccountDeletionRequest: Obiekt zarejestrowanego wniosku o usunięcie.

    Raises:
        TypeError: Gdy parametr reason nie jest napisem.
    """
    if not isinstance(reason, str):
        raise TypeError('Argument reason musi być typu str.')

    reason_clean = (reason or '').strip()[:2000]
    original_email = user.email if hasattr(user, 'email') else ''

    DeviceToken.objects.filter(user=user, is_active=True).update(
        is_active=False,
        updated_at=timezone.now(),
    )

    deletion, _created = AccountDeletionRequest.objects.get_or_create(user=user)
    if reason_clean:
        deletion.reason = reason_clean
    if original_email and not original_email.startswith('deleted-'):
        note = f'email_at_request={original_email}'
        if deletion.notes:
            if note not in deletion.notes:
                deletion.notes = f'{deletion.notes}\n{note}'
        else:
            deletion.notes = note
    deletion.save()

    anonymize_user_for_deletion(user, reason=reason_clean, source='user_request')
    return deletion


def anonymize_user_for_deletion(
    user: object,
    *,
    reason: str = '',
    source: str = 'user_request',
) -> None:
    """Wykonuje anonimizację danych osobowych (soft-delete): czyszczenie PII, deaktywację i unieważnienie haseł.

    Args:
        user (object): Obiekt użytkownika.
        reason (str): Uzasadnienie usunięcia.
        source (str): Źródło operacji ('user_request' lub 're_registration').

    Raises:
        TypeError: Gdy parametry reason lub source nie są napisami.
    """
    if not isinstance(reason, str) or not isinstance(source, str):
        raise TypeError('Parametry reason oraz source muszą być ciągami znaków.')

    user_email = user.email if hasattr(user, 'email') and user.email else ''
    is_active = user.is_active if hasattr(user, 'is_active') else True

    if user_email.startswith('deleted-') and not is_active:
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

    profile = user.patient_profile if hasattr(user, 'patient_profile') else None
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


