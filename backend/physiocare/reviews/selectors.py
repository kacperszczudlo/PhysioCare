from decimal import Decimal

from django.db.models import Count, QuerySet
from django.shortcuts import get_object_or_404

from therapists.models import TherapistProfile

from .models import Review


def review_list_for_therapist_selector(
    therapist_id: str,
    *,
    rating: int | None = None,
    ordering: str = '-created_at',
) -> QuerySet[Review]:
    """Pobiera widoczne opinie danego fizjoterapeuty z optymalizacją zapytań SQL.

    Args:
        therapist_id: Identyfikator UUID profilu fizjoterapeuty.
        rating: Opcjonalna ocena do filtrowania (1-5).
        ordering: Pole i kierunek sortowania.

    Returns:
        QuerySet[Review]: Queryset opinii ze wstępnym dociągnięciem relacji.
    """
    qs = Review.objects.select_related(
        'patient__user',
        'therapist__user',
        'visit',
    ).filter(
        therapist_id=therapist_id,
        is_visible=True,
    )
    if rating is not None:
        qs = qs.filter(rating=rating)

    allowed_orderings = {'created_at', '-created_at', 'rating', '-rating'}
    if ordering in allowed_orderings:
        qs = qs.order_by(ordering)
    return qs


def therapist_rating_summary_selector(therapist_id: str) -> dict[str, object]:
    """Agreguje statystyki ocen dla danego fizjoterapeuty.

    Args:
        therapist_id: Identyfikator UUID profilu fizjoterapeuty.

    Returns:
        dict[str, object]: Średnia ocena, liczba opinii i rozkład ocen 1-5.
    """
    therapist = get_object_or_404(TherapistProfile, pk=therapist_id, user__is_active=True)
    breakdown_qs = (
        Review.objects.filter(
            therapist=therapist,
            is_visible=True,
        )
        .values('rating')
        .annotate(count=Count('id'))
    )

    breakdown: dict[str, int] = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0}
    for row in breakdown_qs:
        breakdown[str(row['rating'])] = row['count']

    return {
        'average_rating': Decimal(str(therapist.rating_avg)),
        'total_reviews': therapist.rating_count,
        'rating_breakdown': breakdown,
    }
