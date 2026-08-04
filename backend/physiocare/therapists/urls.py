from django.urls import path

from .views import (
    TherapistDashboardStatsView,
    TherapistProfileView,
    TherapistPublicView,
)

urlpatterns = [
    path('therapist/profile/', TherapistProfileView.as_view(), name='therapist-profile'),
    path(
        'therapist/dashboard/stats/',
        TherapistDashboardStatsView.as_view(),
        name='therapist-dashboard-stats',
    ),
    path('therapists/<uuid:pk>/public/', TherapistPublicView.as_view(), name='therapist-public'),
]
