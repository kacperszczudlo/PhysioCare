from django.urls import URLPattern, URLResolver, path

from .views import DocumentDownloadView, MeDocumentsListView, TherapistDocumentUploadView

urlpatterns: list[URLPattern | URLResolver] = [
    path(
        'therapist/documents/',
        TherapistDocumentUploadView.as_view(),
        name='therapist-documents',
    ),
    path('<uuid:pk>/download/', DocumentDownloadView.as_view(), name='document-download'),
]

me_urlpatterns: list[URLPattern | URLResolver] = [
    path('documents/', MeDocumentsListView.as_view(), name='me-documents'),
]
