from django.urls import path

from .views import (
    MeDeviceTokenView,
    MeEventsView,
    MeNotificationPreferencesView,
    SseStatsView,
)

me_urlpatterns = [
    path(
        'events/',
        MeEventsView.as_view(),
        name='me-events',
    ),
    path(
        'events/stats/',
        SseStatsView.as_view(),
        name='me-events-stats',
    ),
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
