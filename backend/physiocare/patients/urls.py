from django.urls import path

from core.avatar_views import MeAvatarUploadView

from .views import (
    MeAccountDeletionRequestView,
    MeConsentsView,
    MeDataExportView,
    MeOptionalConsentsView,
    MeProfileView,
    MeTherapistLinkView,
    MeTherapistsView,
    MeTherapistUnlinkView,
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
    path('therapists/', MeTherapistsView.as_view(), name='me-therapists'),
    path('therapists/link/', MeTherapistLinkView.as_view(), name='me-therapist-link'),
    path('therapists/<uuid:therapist_id>/', MeTherapistUnlinkView.as_view(), name='me-therapist-unlink'),
    path('consents/', MeConsentsView.as_view(), name='me-consents'),
    path('consents/optional/', MeOptionalConsentsView.as_view(), name='me-consents-optional'),
    path('data-export/', MeDataExportView.as_view(), name='me-data-export'),
    path(
        'account-deletion-request/',
        MeAccountDeletionRequestView.as_view(),
        name='me-account-deletion-request',
    ),
]
