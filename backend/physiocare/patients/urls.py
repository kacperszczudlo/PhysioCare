from django.urls import path

from core.avatar_views import MeAvatarUploadView

from .views import (
    MeAccountDeletionRequestView,
    MeConsentsView,
    MeDataExportView,
    MeOptionalConsentsView,
    MeProfileView,
    PatientDetailView,
    PatientListView,
)

urlpatterns = [
    path('', PatientListView.as_view(), name='patient-list'),
    path('<uuid:pk>/', PatientDetailView.as_view(), name='patient-detail'),
]

me_urlpatterns = [
    path('profile/', MeProfileView.as_view(), name='me-profile'),
    path('profile/avatar/', MeAvatarUploadView.as_view(), name='me-profile-avatar'),
    path('consents/', MeConsentsView.as_view(), name='me-consents'),
    path('consents/optional/', MeOptionalConsentsView.as_view(), name='me-consents-optional'),
    path('data-export/', MeDataExportView.as_view(), name='me-data-export'),
    path(
        'account-deletion-request/',
        MeAccountDeletionRequestView.as_view(),
        name='me-account-deletion-request',
    ),
]
