import pytest

from notifications.models import DevicePlatform, DeviceToken, NotificationDelivery, NotificationPreference


@pytest.mark.django_db
def test_notification_preference_methods(patient: object) -> None:
    """Sprawdza działanie metody is_preference_enabled w modelu NotificationPreference."""
    # Arrange
    pref: NotificationPreference = NotificationPreference.objects.create(
        user=patient.user,
        pref_key='visit_reminder',
        enabled=True,
    )
    # Assert
    assert pref.is_preference_enabled() is True
    assert str(pref) == f'{patient.user.email} - visit_reminder'


@pytest.mark.django_db
def test_device_token_matches_platform(patient: object) -> None:
    """Sprawdza działanie metody matches_platform oraz weryfikację typów."""
    # Arrange
    token: DeviceToken = DeviceToken(
        user=patient.user,
        expo_push_token='ExponentPushToken[123]',
        platform=DevicePlatform.IOS,
    )
    # Assert
    assert token.matches_platform('ios') is True
    assert token.matches_platform('android') is False
    # Act

    with pytest.raises(TypeError, match="Argument 'target_platform' musi być typu str."):
        token.matches_platform(12345)  # type: ignore[arg-type]


@pytest.mark.django_db
def test_notification_delivery_is_failed(patient: object) -> None:
    """Sprawdza działanie metody is_failed w modelu NotificationDelivery."""
    # Arrange
    delivery: NotificationDelivery = NotificationDelivery(
        user=patient.user,
        pref_key='visit_reminder',
        channel='push',
        status='failed',
        title='Test',
        body='Body',
    )
    # Assert
    assert delivery.is_failed() is True
    assert str(delivery) == f'{patient.user.email} - visit_reminder - failed'

