from django.conf import settings
from django.http import HttpRequest
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Klasa uwierzytelniająca JWT z obsługą tokenów w ciasteczkach HTTP-only.

    Najpierw sprawdza standardowy nagłówek Authorization, a w przypadku jego braku
    odczytuje token dostępowy z ciasteczka HTTP.
    """

    def authenticate(self, request: HttpRequest | Request | None) -> tuple[object, object] | None:
        """Uwierzytelnia żądanie HTTP na podstawie nagłówka lub ciasteczka.

        Args:
            request (HttpRequest | Request | None): Obiekt żądania HTTP.

        Returns:
            tuple[object, object] | None: Krotka zawierająca obiekt użytkownika i zweryfikowany token, lub None jeśli brak tokenu.

        Raises:
            TypeError: Gdy podany argument request ma niepoprawny typ.
        """
        if request is not None and not isinstance(request, (HttpRequest, Request)):
            raise TypeError("Argument 'request' musi być instancją HttpRequest lub Request.")

        if request is None:
            return None

        header = self.get_header(request)
        if header is not None:
            return super().authenticate(request)

        cookie_name = settings.SIMPLE_JWT.get('AUTH_COOKIE_ACCESS', 'access_token')
        cookies = request.COOKIES if hasattr(request, 'COOKIES') else {}
        raw_token = cookies.get(cookie_name)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
