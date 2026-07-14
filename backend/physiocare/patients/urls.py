from django.urls import path

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
    path('consents/', MeConsentsView.as_view(), name='me-consents'),
    path('consents/optional/', MeOptionalConsentsView.as_view(), name='me-consents-optional'),
    path('data-export/', MeDataExportView.as_view(), name='me-data-export'),
    path(
        'account-deletion-request/',
        MeAccountDeletionRequestView.as_view(),
        name='me-account-deletion-request',
    ),
]
