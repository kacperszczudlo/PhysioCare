from django.urls import URLPattern, URLResolver, path

from .views import (
    ReviewDeleteView,
    ReviewEditView,
    ReviewReplyView,
    TherapistDirectReviewCreateView,
    TherapistRatingSummaryView,
    TherapistReviewListView,
    VisitReviewCreateView,
)

urlpatterns: list[URLPattern | URLResolver] = [
    # Publiczne — lista i podsumowanie ocen terapeuty
    path(
        'therapists/<uuid:therapist_id>/reviews/',
        TherapistReviewListView.as_view(),
        name='therapist-reviews-list',
    ),
    path(
        'therapists/<uuid:therapist_id>/rating-summary/',
        TherapistRatingSummaryView.as_view(),
        name='therapist-rating-summary',
    ),
    path(
        'therapists/<uuid:therapist_id>/reviews/create/',
        TherapistDirectReviewCreateView.as_view(),
        name='therapist-review-create',
    ),
    # Chronione — pacjent wystawia opinię
    path(
        'visits/<uuid:visit_id>/review/',
        VisitReviewCreateView.as_view(),
        name='visit-review-create',
    ),
    # Chronione — pacjent edytuje / usuwa własną opinię
    path(
        'reviews/<uuid:pk>/edit/',
        ReviewEditView.as_view(),
        name='review-edit',
    ),
    path(
        'reviews/<uuid:pk>/delete/',
        ReviewDeleteView.as_view(),
        name='review-delete',
    ),
    # Chronione — terapeuta odpowiada na opinię
    path(
        'reviews/<uuid:review_id>/reply/',
        ReviewReplyView.as_view(),
        name='review-reply',
    ),
]
