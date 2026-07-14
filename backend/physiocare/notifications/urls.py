from django.urls import path

from .views import MeNotificationPreferencesView

me_urlpatterns = [
    path(
        'notification-preferences/',
        MeNotificationPreferencesView.as_view(),
        name='me-notification-preferences',
    ),
]

urlpatterns = []
