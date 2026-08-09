"""Query helpers for therapist exercise catalog filters."""

from __future__ import annotations

import uuid

from django.db.models import Q, QuerySet

from .models import CategoryKind, ExerciseCategory

KIND_QUERY_PARAMS = {
    'type': CategoryKind.TYPE,
    'region': CategoryKind.REGION,
    'muscle': CategoryKind.MUSCLE,
    'injury': CategoryKind.INJURY,
}


def _param_values(query_params, key: str) -> list[str]:
    """Collect repeated and comma-separated query values."""
    values: list[str] = []
    for raw in query_params.getlist(key):
        for part in str(raw).split(','):
            token = part.strip()
            if token:
                values.append(token)
    return values


def _split_ids_and_slugs(tokens: list[str]) -> tuple[list[str], list[str]]:
    ids: list[str] = []
    slugs: list[str] = []
    for token in tokens:
        try:
            ids.append(str(uuid.UUID(token)))
        except (ValueError, AttributeError, TypeError):
            slugs.append(token)
    return ids, slugs


def _category_token_q(tokens: list[str]) -> Q | None:
    ids, slugs = _split_ids_and_slugs(tokens)
    query = Q()
    if ids:
        query |= Q(pk__in=ids)
    if slugs:
        query |= Q(slug__in=slugs)
    if not ids and not slugs:
        return None
    return query


def filter_exercises_queryset(qs: QuerySet, query_params) -> QuerySet:
    """
    Apply catalog filters.

    - category: UUID or slug (OR within values)
    - type / region / muscle / injury: UUID or slug for that kind (OR within kind)
    - Cross-kind filters are AND (exercise must match each selected dimension)
    - media_type, q: title/instruction search
    """
    category_tokens = _param_values(query_params, 'category')
    if category_tokens:
        ids, slugs = _split_ids_and_slugs(category_tokens)
        cat_q = Q()
        if ids:
            cat_q |= Q(categories__id__in=ids)
        if slugs:
            cat_q |= Q(categories__slug__in=slugs)
        if ids or slugs:
            qs = qs.filter(cat_q).distinct()

    for param, kind in KIND_QUERY_PARAMS.items():
        tokens = _param_values(query_params, param)
        if not tokens:
            continue
        token_q = _category_token_q(tokens)
        if token_q is None:
            return qs.none()
        ids = list(
            ExerciseCategory.objects.filter(kind=kind)
            .filter(token_q)
            .values_list('pk', flat=True)
        )
        if not ids:
            return qs.none()
        qs = qs.filter(categories__in=ids).distinct()

    media_type = query_params.get('media_type')
    if media_type:
        qs = qs.filter(media_type=media_type)

    search = query_params.get('q')
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(instruction__icontains=search))

    return qs
