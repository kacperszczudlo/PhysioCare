from django.urls import path

from .views import (
    EpisodeBodyPainDetailView,
    EpisodeBodyPainListCreateView,
    EpisodeDetailView,
    EpisodeNoteListCreateView,
    PatientEpisodeListCreateView,
)

urlpatterns = [
    path(
        'patients/<uuid:patient_id>/episodes/',
        PatientEpisodeListCreateView.as_view(),
        name='patient-episodes',
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
]
