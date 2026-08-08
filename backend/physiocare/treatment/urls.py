from django.urls import path

from .views import (
    EpisodeBodyPainDetailView,
    EpisodeBodyPainListCreateView,
    EpisodeDetailView,
    EpisodeDeviceOrderListCreateView,
    EpisodeDiagnosticRecommendationListCreateView,
    EpisodeNoteListCreateView,
    EpisodeOrderRefusalListCreateView,
    MedicalDeviceCatalogView,
    PatientEpisodeListCreateView,
    PatientReceptaNaRuchListCreateView,
)

urlpatterns = [
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
        'episodes/<uuid:episode_id>/device-orders/',
        EpisodeDeviceOrderListCreateView.as_view(),
        name='episode-device-orders',
    ),
    path(
        'episodes/<uuid:episode_id>/order-refusals/',
        EpisodeOrderRefusalListCreateView.as_view(),
        name='episode-order-refusals',
    ),
    path(
        'medical-devices/catalog/',
        MedicalDeviceCatalogView.as_view(),
        name='medical-device-catalog',
    ),
]
