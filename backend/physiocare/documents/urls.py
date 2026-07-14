from django.urls import path

from .views import DocumentDownloadView, MeDocumentsListView, TherapistDocumentUploadView

urlpatterns = [
    path(
        'therapist/documents/',
        TherapistDocumentUploadView.as_view(),
        name='therapist-documents',
    ),
    path('<uuid:pk>/download/', DocumentDownloadView.as_view(), name='document-download'),
]

me_urlpatterns = [
    path('documents/', MeDocumentsListView.as_view(), name='me-documents'),
]
