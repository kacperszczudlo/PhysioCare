from notifications.defaults import ensure_default_preferences
from notifications.keys import CANONICAL_PREF_KEYS
from notifications.models import DeviceToken, NotificationDelivery, NotificationPreference


def _token_fingerprint(token: str) -> str:
    value = (token or '').strip()
    if len(value) < 8:
        return '***'
    return f'…{value[-8:]}'


def notification_export_payload(user) -> dict:
    ensure_default_preferences(user)
    prefs = {
        item.pref_key: item.enabled
        for item in NotificationPreference.objects.filter(
            user=user,
            pref_key__in=CANONICAL_PREF_KEYS,
        )
    }
    devices = DeviceToken.objects.filter(user=user).order_by('-updated_at')
    deliveries = NotificationDelivery.objects.filter(user=user).order_by('-created_at')[:100]
    return {
        'notification_preferences': [
            {'pref_key': key, 'enabled': prefs.get(key, True)}
            for key in CANONICAL_PREF_KEYS
        ],
        'device_tokens': [
            {
                'id': str(device.id),
                'platform': device.platform,
                'is_active': device.is_active,
                'updated_at': device.updated_at.isoformat(),
                'token_fingerprint': _token_fingerprint(device.expo_push_token),
            }
            for device in devices
        ],
        'notification_deliveries': [
            {
                'pref_key': item.pref_key,
                'channel': item.channel,
                'status': item.status,
                'title': item.title,
                'body': item.body,
                'data': item.data,
                'created_at': item.created_at.isoformat(),
            }
            for item in deliveries
        ],
    }
