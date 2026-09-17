from unittest.mock import patch

import pytest

from notifications.delivery import notify_user
from notifications.models import DeviceToken


@pytest.mark.django_db
@patch('notifications.delivery.send_expo_push')
def test_expo_push_device_not_registered_disables_token(
    mock_send_push: object, patient: object,
) -> None:
    """Gdy Expo Push API zwraca błąd DeviceNotRegistered, stary token urządzenia zostaje deaktywowany."""
    # Arrange
    user: object = patient.user
    token_str: str = 'ExpoPushToken[UnregisteredDevice123]'
    device_token: DeviceToken = DeviceToken.objects.create(
        user=user,
        expo_push_token=token_str,
        is_active=True,
    )

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
    # Assert
    assert device_token.is_active is False

