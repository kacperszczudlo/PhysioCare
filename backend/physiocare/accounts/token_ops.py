"""Refresh-token blacklist helpers (SimpleJWT outstanding tokens)."""

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken


def blacklist_refresh_value(raw: str | None) -> None:
    if not raw or not isinstance(raw, str):
        return
    try:
        RefreshToken(raw).blacklist()
    except TokenError:
        return


def blacklist_user_refresh_tokens(user) -> None:
    if user is None or not getattr(user, 'pk', None):
        return
    for outstanding in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=outstanding)


def wants_tokens_in_body(request) -> bool:
    data = getattr(request, 'data', None)
    delivery = ''
    if isinstance(data, dict):
        delivery = str(data.get('token_delivery') or '').strip().lower()
    header = ''
    headers = getattr(request, 'headers', None)
    if headers is not None:
        header = str(headers.get('X-PhysioCare-Token-Delivery', '')).strip().lower()
    return delivery != 'cookie' and header != 'cookie'
