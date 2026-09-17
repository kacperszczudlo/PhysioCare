from django.http import HttpRequest
from rest_framework.request import Request
from rest_framework.throttling import SimpleRateThrottle


class LoginRateThrottle(SimpleRateThrottle):
    """Ograniczenie liczby prób logowania dla niezalogowanych użytkowników."""

    scope: str = 'login'

    def get_cache_key(self, request: Request | HttpRequest, view: object) -> str | None:
        """Generuje klucz pamięci podręcznej dla limitu prób logowania.

        Args:
            request (Request | HttpRequest): Obiekt żądania HTTP.
            view (object): Widok DRF.

        Returns:
            str | None: Klucz pamięci podręcznej lub None, jeśli użytkownik jest uwierzytelniony.

        Raises:
            TypeError: Gdy request nie jest instancją Request ani HttpRequest.
        """
        if not isinstance(request, (Request, HttpRequest)):
            raise TypeError("Argument 'request' musi być instancją Request lub HttpRequest.")

        if request.user and request.user.is_authenticated:
            return None
        ident: str = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class RegisterRateThrottle(SimpleRateThrottle):
    """Ograniczenie liczby prób rejestracji konta z danego adresu IP."""

    scope: str = 'register'

    def get_cache_key(self, request: Request | HttpRequest, view: object) -> str | None:
        """Generuje klucz pamięci podręcznej dla limitu prób rejestracji.

        Args:
            request (Request | HttpRequest): Obiekt żądania HTTP.
            view (object): Widok DRF.

        Returns:
            str | None: Klucz pamięci podręcznej wygenerowany na podstawie identyfikatora żądania.

        Raises:
            TypeError: Gdy request nie jest instancją Request ani HttpRequest.
        """
        if not isinstance(request, (Request, HttpRequest)):
            raise TypeError("Argument 'request' musi być instancją Request lub HttpRequest.")

        ident: str = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class PasswordResetRateThrottle(SimpleRateThrottle):
    """Ograniczenie liczby żądań resetowania hasła z danego adresu IP."""

    scope: str = 'password_reset'

    def get_cache_key(self, request: Request | HttpRequest, view: object) -> str | None:
        """Generuje klucz pamięci podręcznej dla limitu resetowania hasła.

        Args:
            request (Request | HttpRequest): Obiekt żądania HTTP.
            view (object): Widok DRF.

        Returns:
            str | None: Klucz pamięci podręcznej wygenerowany na podstawie identyfikatora żądania.

        Raises:
            TypeError: Gdy request nie jest instancją Request ani HttpRequest.
        """
        if not isinstance(request, (Request, HttpRequest)):
            raise TypeError("Argument 'request' musi być instancją Request lub HttpRequest.")

        ident: str = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}
