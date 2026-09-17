from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken


def blacklist_refresh_value(raw: str | None) -> None:
    """Dodaje podany token odświeżania do czarnej listy.

    Args:
        raw (str | None): Surowy ciąg tokenu odświeżania.

    Raises:
        TypeError: Gdy raw nie jest typu str lub None.
    """
    if raw is not None and not isinstance(raw, str):
        raise TypeError("Argument 'raw' musi być typu str lub None.")
    if not raw:
        return
    try:
        RefreshToken(raw).blacklist()
    except TokenError:
        return


def blacklist_user_refresh_tokens(user: object) -> None:
    """Unieważnia (wpisuje na czarną listę) wszystkie aktywne tokeny odświeżania danego użytkownika.

    Args:
        user (object): Obiekt użytkownika Django.

    Raises:
        TypeError: Gdy user jest None lub nie posiada atrybutu pk.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")
    if not hasattr(user, 'pk') or user.pk is None:
        raise TypeError("Argument 'user' musi posiadać klucz główny (pk).")

    for outstanding in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=outstanding)


def wants_tokens_in_body(request: object) -> bool:
    """Sprawdza, czy żądanie oczekuje zwrócenia tokenów w treści odpowiedzi (JSON) zamiast w ciasteczkach HTTP-only.

    Args:
        request (object): Obiekt żądania HTTP.

    Returns:
        bool: True jeśli tokeny powinny zostać dodane do body odpowiedzi.

    Raises:
        TypeError: Gdy request jest None.
    """
    if request is None:
        raise TypeError("Argument 'request' nie może być None.")

    data = request.data if hasattr(request, 'data') else None
    delivery = ''
    if isinstance(data, dict):
        delivery = str(data.get('token_delivery') or '').strip().lower()
    header = ''
    headers = request.headers if hasattr(request, 'headers') else None
    if headers is not None and hasattr(headers, 'get'):
        header = str(headers.get('X-PhysioCare-Token-Delivery', '')).strip().lower()
    return delivery != 'cookie' and header != 'cookie'

