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


class AdminPasswordResetRateThrottle(SimpleRateThrottle):
    """Ograniczenie liczby żądań resetowania hasła zlecanych przez administratora."""

    scope: str = 'admin_password_reset'

    def get_cache_key(self, request: Request | HttpRequest, view: object) -> str | None:
        """Generuje klucz pamięci podręcznej dla limitu administracyjnego resetu hasła.

        Args:
            request (Request | HttpRequest): Obiekt żądania HTTP.
            view (object): Widok DRF.

        Returns:
            str | None: Klucz pamięci podręcznej na podstawie ID administratora lub IP.
        """
        if not isinstance(request, (Request, HttpRequest)):
            raise TypeError("Argument 'request' musi być instancją Request lub HttpRequest.")

        user = getattr(request, 'user', None)
        ident = str(user.pk) if user and getattr(user, 'is_authenticated', False) else self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class ExportRateThrottle(SimpleRateThrottle):
    """Ograniczenie częstotliwości generowania pełnych paczek eksportowych danych (RODO Art. 20)."""

    scope: str = 'export'

    def get_cache_key(self, request: Request | HttpRequest, view: object) -> str | None:
        """Generuje klucz pamięci podręcznej dla limitu eksportu danych osobowych.

        Args:
            request (Request | HttpRequest): Obiekt żądania HTTP.
            view (object): Widok DRF.

        Returns:
            str | None: Klucz pamięci podręcznej wygenerowany na podstawie identyfikatora użytkownika lub IP.

        Raises:
            TypeError: Gdy request nie jest instancją Request ani HttpRequest.
        """
        if not isinstance(request, (Request, HttpRequest)):
            raise TypeError("Argument 'request' musi być instancją Request lub HttpRequest.")
        user = getattr(request, 'user', None)
        ident = str(user.pk) if user and getattr(user, 'is_authenticated', False) else self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class VisitBookingRateThrottle(SimpleRateThrottle):
    """Ograniczenie liczby rezerwacji wizyt tworzonych przez pacjenta."""

    scope: str = 'visit_booking'

    def get_cache_key(self, request: Request | HttpRequest, view: object) -> str | None:
        """Generuje klucz pamięci podręcznej dla limitu rezerwacji wizyt.

        Args:
            request (Request | HttpRequest): Obiekt żądania HTTP.
            view (object): Widok DRF.

        Returns:
            str | None: Klucz pamięci podręcznej wygenerowany na podstawie identyfikatora użytkownika lub IP.

        Raises:
            TypeError: Gdy request nie jest instancją Request ani HttpRequest.
        """
        if not isinstance(request, (Request, HttpRequest)):
            raise TypeError("Argument 'request' musi być instancją Request lub HttpRequest.")
        user = getattr(request, 'user', None)
        ident = str(user.pk) if user and getattr(user, 'is_authenticated', False) else self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class DocumentUploadRateThrottle(SimpleRateThrottle):
    """Ograniczenie liczby wgrywanych dokumentów medycznych w jednostce czasu."""

    scope: str = 'document_upload'

    def get_cache_key(self, request: Request | HttpRequest, view: object) -> str | None:
        """Generuje klucz pamięci podręcznej dla limitu wgrywania dokumentów medycznych.

        Args:
            request (Request | HttpRequest): Obiekt żądania HTTP.
            view (object): Widok DRF.

        Returns:
            str | None: Klucz pamięci podręcznej wygenerowany na podstawie identyfikatora użytkownika lub IP.

        Raises:
            TypeError: Gdy request nie jest instancją Request ani HttpRequest.
        """
        if not isinstance(request, (Request, HttpRequest)):
            raise TypeError("Argument 'request' musi być instancją Request lub HttpRequest.")
        user = getattr(request, 'user', None)
        ident = str(user.pk) if user and getattr(user, 'is_authenticated', False) else self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}



