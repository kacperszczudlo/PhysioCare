from __future__ import annotations

import uuid

from django.db.models import Q, QuerySet

from .models import CategoryKind, ExerciseCategory

KIND_QUERY_PARAMS: dict[str, str] = {
    'type': CategoryKind.TYPE,
    'region': CategoryKind.REGION,
    'muscle': CategoryKind.MUSCLE,
    'injury': CategoryKind.INJURY,
}


def _param_values(query_params: object, key: str) -> list[str]:
    """Pobiera i rozdziela wartości parametrów zapytania rozdzielane przecinkami.

    Args:
        query_params (object): Obiekt parametrów zapytania (np. QueryDict lub dict).
        key (str): Klucz parametru do pobrania.

    Returns:
        list[str]: Lista wyekstrahowanych ciągów znaków (tokenów).

    Raises:
        TypeError: Gdy argument key nie jest napisem.
    """
    if not isinstance(key, str):
        raise TypeError("Argument 'key' musi być typu str.")

    values: list[str] = []
    if query_params is None:
        return values

    raw_list: list[object] = []
    if hasattr(query_params, 'getlist'):
        raw_list = query_params.getlist(key)
    elif hasattr(query_params, 'get'):
        val: object = query_params.get(key)
        raw_list = [val] if val is not None else []
    elif isinstance(query_params, dict):
        val_dict: object = query_params.get(key)
        raw_list = [val_dict] if val_dict is not None else []

    for raw in raw_list:
        for part in str(raw).split(','):
            token: str = part.strip()
            if token:
                values.append(token)
    return values


def _split_ids_and_slugs(tokens: list[str]) -> tuple[list[str], list[str]]:
    """Rozdziela tokeny na identyfikatory UUID oraz slugi.

    Args:
        tokens (list[str]): Lista tokenów tekstowych.

    Returns:
        tuple[list[str], list[str]]: Para zawierająca listę UUID oraz listę slugów.

    Raises:
        TypeError: Gdy argument tokens nie jest listą.
    """
    if not isinstance(tokens, list):
        raise TypeError("Argument 'tokens' musi być listą list[str].")

    ids: list[str] = []
    slugs: list[str] = []
    for token in tokens:
        if not isinstance(token, str):
            continue
        try:
            ids.append(str(uuid.UUID(token)))
        except (ValueError, AttributeError, TypeError):
            slugs.append(token)
    return ids, slugs


def _category_token_q(tokens: list[str]) -> Q | None:
    """Tworzy obiekt zapytania Q do filtrowania po UUID lub slugu.

    Args:
        tokens (list[str]): Lista tokenów tekstowych.

    Returns:
        Q | None: Obiekt zapytania Q lub None, jeśli brak tokenów.

    Raises:
        TypeError: Gdy argument tokens nie jest listą.
    """
    if not isinstance(tokens, list):
        raise TypeError("Argument 'tokens' musi być listą list[str].")

    ids, slugs = _split_ids_and_slugs(tokens)
    query: Q = Q()
    if ids:
        query |= Q(pk__in=ids)
    if slugs:
        query |= Q(slug__in=slugs)
    if not ids and not slugs:
        return None
    return query


def filter_exercises_queryset(qs: QuerySet, query_params: object) -> QuerySet:
    """Filtruje QuerySet ćwiczeń na podstawie przekazanych parametrów zapytania.

    Aplikuje filtry katalogu:
    - category: UUID lub slug (koniunkcja alternatywna OR dla wartości)
    - type / region / muscle / injury: UUID lub slug danej kategorii (OR w ramach typu)
    - Filtry między rożnymi typami są łączone warunkiem AND
    - media_type, q: szukanie po tytule lub instrukcji

    Args:
        qs (QuerySet): Początkowy zestaw danych QuerySet dla ćwiczeń.
        query_params (object): Obiekt parametrów zapytania HTTP.

    Returns:
        QuerySet: Przefiltrowany zestaw danych ćwiczeń.

    Raises:
        TypeError: Jeśli parametr qs nie jest instancją QuerySet.
    """
    if not isinstance(qs, QuerySet):
        raise TypeError('qs musi być instancją QuerySet')

    category_tokens: list[str] = _param_values(query_params, 'category')
    if category_tokens:
        ids, slugs = _split_ids_and_slugs(category_tokens)
        cat_q: Q = Q()
        if ids:
            cat_q |= Q(categories__id__in=ids)
        if slugs:
            cat_q |= Q(categories__slug__in=slugs)
        if ids or slugs:
            qs = qs.filter(cat_q).distinct()

    for param, kind in KIND_QUERY_PARAMS.items():
        tokens: list[str] = _param_values(query_params, param)
        if not tokens:
            continue
        token_q: Q | None = _category_token_q(tokens)
        if token_q is None:
            return qs.none()
        matched_ids: list[object] = list(
            ExerciseCategory.objects.filter(kind=kind)
            .filter(token_q)
            .values_list('pk', flat=True)
        )
        if not matched_ids:
            return qs.none()
        qs = qs.filter(categories__in=matched_ids).distinct()

    media_type: object = None
    if hasattr(query_params, 'get'):
        media_type = query_params.get('media_type')
    elif isinstance(query_params, dict):
        media_type = query_params.get('media_type')

    if media_type:
        qs = qs.filter(media_type=media_type)

    search: object = None
    if hasattr(query_params, 'get'):
        search = query_params.get('q')
    elif isinstance(query_params, dict):
        search = query_params.get('q')

    if search:
        qs = qs.filter(Q(title__icontains=str(search)) | Q(instruction__icontains=str(search)))

    return qs
