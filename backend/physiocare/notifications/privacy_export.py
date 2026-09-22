from notifications.defaults import ensure_default_preferences
from notifications.keys import CANONICAL_PREF_KEYS
from notifications.models import DeviceToken, NotificationDelivery, NotificationPreference


def _token_fingerprint(token: str) -> str:
    """Generuje skróconą maskę (odcisk) dla tokenu urządzenia ze względów bezpieczeństwa.

    Args:
        token (str): Całkowity ciąg znaków tokenu.

    Returns:
        str: Zamaskowany ciąg znaków z końcowym fragmentem tokenu.

    Raises:
        TypeError: Gdy argument token nie jest napisem.
    """
    if not isinstance(token, str):
        raise TypeError("Argument 'token' musi być typu str.")

    value: str = token.strip()
    if len(value) < 8:
        return '***'
    return f'…{value[-8:]}'


def notification_export_payload(user: object) -> dict[str, object]:
    """Eksportuje dane powiadomień użytkownika w ramach RODO/Privacy Export.

    Args:
        user (object): Obiekt użytkownika, dla którego pobierane są dane.

    Returns:
        dict[str, object]: Słownik zawierający preferencje, zarejestrowane urządzenia i historię dostarczeń.

    Raises:
        TypeError: Gdy argument user jest None.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")

    ensure_default_preferences(user)
    prefs: dict[str, bool] = {
        item.pref_key: item.enabled
        for item in NotificationPreference.objects.filter(
            user=user,
            pref_key__in=CANONICAL_PREF_KEYS,
        )
    }
    devices: object = DeviceToken.objects.filter(user=user).order_by('-updated_at')
    deliveries: object = NotificationDelivery.objects.filter(user=user).order_by('-created_at')[:100]
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
            for device in devices  # type: ignore[union-attr]
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
            for item in deliveries  # type: ignore[union-attr]
        ],
    }
