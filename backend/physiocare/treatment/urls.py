from django.urls import URLPattern, URLResolver, path

from .views import (
    EpisodeBodyPainDetailView,
    EpisodeBodyPainListCreateView,
    EpisodeDetailView,
    EpisodeDeviceOrderDetailView,
    EpisodeDeviceOrderListCreateView,
    EpisodeDiagnosticRecommendationDetailView,
    EpisodeDiagnosticRecommendationListCreateView,
    EpisodeNoteListCreateView,
    EpisodeOrderRefusalDetailView,
    EpisodeOrderRefusalListCreateView,
    MeClinicalDocumentsListView,
    MedicalDeviceCatalogView,
    MeEpisodeDetailView,
    MeEpisodeListView,
    PatientEpisodeListCreateView,
    PatientReceptaNaRuchDetailView,
    PatientReceptaNaRuchListCreateView,
)

urlpatterns: list[URLPattern | URLResolver] = [
    path(
        'patients/<uuid:patient_id>/episodes/',
        PatientEpisodeListCreateView.as_view(),
        name='patient-episodes',
    ),
    path(
        'patients/<uuid:patient_id>/recepta-na-ruch/',
        PatientReceptaNaRuchListCreateView.as_view(),
        name='patient-recepta-na-ruch',
    ),
    path(
        'patients/<uuid:patient_id>/recepta-na-ruch/<uuid:pk>/',
        PatientReceptaNaRuchDetailView.as_view(),
        name='patient-recepta-na-ruch-detail',
    ),
    path('episodes/<uuid:pk>/', EpisodeDetailView.as_view(), name='episode-detail'),
    path(
        'episodes/<uuid:episode_id>/body-pain/',
        EpisodeBodyPainListCreateView.as_view(),
        name='episode-body-pain',
    ),
    path(
        'episodes/<uuid:episode_id>/body-pain/<uuid:pk>/',
        EpisodeBodyPainDetailView.as_view(),
        name='episode-body-pain-detail',
    ),
    path(
        'episodes/<uuid:episode_id>/notes/',
        EpisodeNoteListCreateView.as_view(),
        name='episode-notes',
    ),
    path(
        'episodes/<uuid:episode_id>/diagnostic-recommendations/',
        EpisodeDiagnosticRecommendationListCreateView.as_view(),
        name='episode-diagnostic-recommendations',
    ),
    path(
        'episodes/<uuid:episode_id>/diagnostic-recommendations/<uuid:pk>/',
        EpisodeDiagnosticRecommendationDetailView.as_view(),
        name='episode-diagnostic-recommendation-detail',
    ),
    path(
        'episodes/<uuid:episode_id>/device-orders/',
        EpisodeDeviceOrderListCreateView.as_view(),
        name='episode-device-orders',
    ),
    path(
        'episodes/<uuid:episode_id>/device-orders/<uuid:pk>/',
        EpisodeDeviceOrderDetailView.as_view(),
        name='episode-device-order-detail',
    ),
    path(
        'episodes/<uuid:episode_id>/order-refusals/',
        EpisodeOrderRefusalListCreateView.as_view(),
        name='episode-order-refusals',
    ),
    path(
        'episodes/<uuid:episode_id>/order-refusals/<uuid:pk>/',
        EpisodeOrderRefusalDetailView.as_view(),
        name='episode-order-refusal-detail',
    ),
    path(
        'medical-devices/catalog/',
        MedicalDeviceCatalogView.as_view(),
        name='medical-device-catalog',
    ),
]

me_urlpatterns: list[URLPattern | URLResolver] = [
    path(
        'clinical-documents/',
        MeClinicalDocumentsListView.as_view(),
        name='me-clinical-documents',
    ),
    path('episodes/', MeEpisodeListView.as_view(), name='me-episodes'),
    path('episodes/<uuid:pk>/', MeEpisodeDetailView.as_view(), name='me-episode-detail'),
]
