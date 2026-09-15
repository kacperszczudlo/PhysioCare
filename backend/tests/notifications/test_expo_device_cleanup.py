from unittest.mock import patch

import pytest

from notifications.delivery import notify_user
from notifications.models import DeviceToken


@pytest.mark.django_db
@patch('notifications.delivery.send_expo_push')
def test_expo_push_device_not_registered_disables_token(mock_send_push, patient):
    """Gdy Expo Push API zwraca błąd DeviceNotRegistered, stary token urządzenia zostaje deaktywowany."""
    user = patient.user
    token_str = 'ExpoPushToken[UnregisteredDevice123]'
    device_token = DeviceToken.objects.create(
        user=user,
        expo_push_token=token_str,
        is_active=True,
    )

    # Symulacja odpowiedzi z serwera Expo o wyrejestrowanym urządzeniu
    mock_send_push.return_value = [
        {
            'status': 'error',
            'details': {'error': 'DeviceNotRegistered'},
            'message': 'Device is no longer registered',
        }
    ]

    notify_user(
        user=user,
        pref_key='visit_reminder',
        title='Przypomnienie',
        body='Wizyta jutro',
    )

    device_token.refresh_from_db()
    assert device_token.is_active is False
