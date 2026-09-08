from django.urls import path

from .views import MeDeviceTokenView, MeNotificationPreferencesView

me_urlpatterns = [
    path(
        'notification-preferences/',
        MeNotificationPreferencesView.as_view(),
        name='me-notification-preferences',
    ),
    path(
        'device-tokens/',
        MeDeviceTokenView.as_view(),
        name='me-device-tokens',
    ),
]

urlpatterns = []
