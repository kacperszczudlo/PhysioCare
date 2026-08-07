from django.urls import path

from .views import (
    MeVisitListView,
    TherapistVisitDetailView,
    TherapistVisitListCreateView,
    TherapyTypeListCreateView,
    TherapyTypePresetListView,
    TherapyTypeSeedPresetsView,
    VisitCancelView,
    VisitDetailView,
    VisitRescheduleView,
)

urlpatterns = [
    path(
        'therapist/visits/',
        TherapistVisitListCreateView.as_view(),
        name='therapist-visits',
    ),
    path(
        'therapist/visits/<uuid:pk>/',
        TherapistVisitDetailView.as_view(),
        name='therapist-visit-detail',
    ),
    path(
        'therapist/therapy-types/',
        TherapyTypeListCreateView.as_view(),
        name='therapy-types',
    ),
    path(
        'therapist/therapy-types/presets/',
        TherapyTypePresetListView.as_view(),
        name='therapy-type-presets',
    ),
    path(
        'therapist/therapy-types/seed-presets/',
        TherapyTypeSeedPresetsView.as_view(),
        name='therapy-type-seed-presets',
    ),
    path('visits/<uuid:pk>/', VisitDetailView.as_view(), name='visit-detail'),
    path(
        'visits/<uuid:pk>/reschedule/',
        VisitRescheduleView.as_view(),
        name='visit-reschedule',
    ),
    path('visits/<uuid:pk>/cancel/', VisitCancelView.as_view(), name='visit-cancel'),
]

me_urlpatterns = [
    path('visits/', MeVisitListView.as_view(), name='me-visits'),
]
