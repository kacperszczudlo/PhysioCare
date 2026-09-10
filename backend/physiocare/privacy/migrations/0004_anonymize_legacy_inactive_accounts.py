from django.db import migrations


def anonymize_legacy_inactive_accounts(apps, schema_editor):
    User = apps.get_model('accounts', 'CustomUser')
    AccountDeletionRequest = apps.get_model('privacy', 'AccountDeletionRequest')
    PatientProfile = apps.get_model('patients', 'PatientProfile')
    DeviceToken = apps.get_model('notifications', 'DeviceToken')

    inactive_ids = set(
        User.objects.filter(is_active=False)
        .exclude(email__startswith='deleted-')
        .values_list('id', flat=True)
    )
    requested_ids = set(
        AccountDeletionRequest.objects.values_list('user_id', flat=True)
    )
    target_ids = inactive_ids | requested_ids

    for user in User.objects.filter(id__in=target_ids).exclude(email__startswith='deleted-'):
        original = user.email
        user.email = f'deleted-{user.id}@deleted.invalid'
        user.first_name = 'Usunięte'
        user.last_name = 'Konto'
        user.google_sub = None
        user.email_verified_at = None
        user.is_active = False
        user.save(
            update_fields=[
                'email',
                'first_name',
                'last_name',
                'google_sub',
                'email_verified_at',
                'is_active',
                'updated_at',
            ]
        )
        PatientProfile.objects.filter(user_id=user.id).update(
            pesel=None,
            phone='',
            avatar_url='',
        )
        DeviceToken.objects.filter(user_id=user.id, is_active=True).update(is_active=False)
        deletion, _ = AccountDeletionRequest.objects.get_or_create(user_id=user.id)
        note = f'email_at_request={original}'
        if note not in (deletion.notes or ''):
            deletion.notes = f'{deletion.notes}\n{note}'.strip() if deletion.notes else note
            if not deletion.reason:
                deletion.reason = 'Migracja: anonimizacja wcześniej wyłączonego konta.'
            deletion.save(update_fields=['notes', 'reason'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('privacy', '0003_accountdeletionrequest_reason'),
        ('patients', '0002_ordering'),
        ('notifications', '0003_device_token_and_delivery'),
        ('accounts', '0003_email_verified_and_email_codes'),
    ]

    operations = [
        migrations.RunPython(anonymize_legacy_inactive_accounts, noop_reverse),
    ]
