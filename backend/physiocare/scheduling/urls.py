from django.urls import path

from .views import (
    MeTherapyTypeListView,
    MeVisitListCreateView,
    PolishHolidaysView,
    PublicTherapistAvailableSlotsView,
    TherapistAvailabilityDetailView,
    TherapistAvailabilityListCreateView,
    TherapistVisitDetailView,
    TherapistVisitListCreateView,
    TherapyTypeListCreateView,
    TherapyTypePresetListView,
    TherapyTypeSeedPresetsView,
    VisitApproveView,
    VisitCancelView,
    VisitDetailView,
    VisitRejectView,
    VisitRescheduleView,
)

urlpatterns = [
    path('scheduling/holidays/', PolishHolidaysView.as_view(), name='polish-holidays'),
    path(
        'therapist/availabilities/',
        TherapistAvailabilityListCreateView.as_view(),
        name='therapist-availabilities',
    ),
    path(
        'therapist/availabilities/<uuid:pk>/',
        TherapistAvailabilityDetailView.as_view(),
        name='therapist-availability-detail',
    ),
    path(
        'therapists/<uuid:therapist_id>/available-slots/',
        PublicTherapistAvailableSlotsView.as_view(),
        name='public-therapist-available-slots',
    ),
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
        'therapist/visits/<uuid:pk>/approve/',
        VisitApproveView.as_view(),
        name='therapist-visit-approve',
    ),
    path(
        'therapist/visits/<uuid:pk>/reject/',
        VisitRejectView.as_view(),
        name='therapist-visit-reject',
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
    path('visits/', MeVisitListCreateView.as_view(), name='me-visits'),
    path('therapy-types/', MeTherapyTypeListView.as_view(), name='me-therapy-types'),
]
