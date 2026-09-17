from rest_framework import permissions


class IsPatient(permissions.BasePermission):
    """Uprawnienie sprawdzające, czy użytkownik jest zalogowany i ma rolę pacjenta."""

    def has_permission(self, request: object, view: object) -> bool:
        """Sprawdza uprawnienie dostępności dla widoku.

        Args:
            request (object): Obiekt żądania HTTP.
            view (object): Widok DRF.

        Returns:
            bool: True, jeśli użytkownik jest zalogowany i posiada rolę PATIENT.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        user = request.user if hasattr(request, 'user') else None
        is_authenticated = user.is_authenticated if user is not None and hasattr(user, 'is_authenticated') else False
        role = user.role if user is not None and hasattr(user, 'role') else None

        return bool(user and is_authenticated and role == 'PATIENT')


class IsTherapist(permissions.BasePermission):
    """Uprawnienie sprawdzające, czy użytkownik jest zalogowany i ma rolę terapeuty."""

    def has_permission(self, request: object, view: object) -> bool:
        """Sprawdza uprawnienie dostępności dla widoku.

        Args:
            request (object): Obiekt żądania HTTP.
            view (object): Widok DRF.

        Returns:
            bool: True, jeśli użytkownik jest zalogowany i posiada rolę THERAPIST.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        user = request.user if hasattr(request, 'user') else None
        is_authenticated = user.is_authenticated if user is not None and hasattr(user, 'is_authenticated') else False
        role = user.role if user is not None and hasattr(user, 'role') else None

        return bool(user and is_authenticated and role == 'THERAPIST')


class IsOwnerPatientProfile(permissions.BasePermission):
    """Uprawnienie sprawdzające dostęp do profilu pacjenta."""

    def has_object_permission(self, request: object, view: object, obj: object) -> bool:
        """Sprawdza, czy użytkownik ma dostęp do wskazanego profilu pacjenta.

        Args:
            request (object): Obiekt żądania HTTP.
            view (object): Widok DRF.
            obj (object): Obiekt pacjenta.

        Returns:
            bool: True, jeśli użytkownik ma prawo dostępu do profilu pacjenta.

        Raises:
            TypeError: Gdy request lub obj jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")
        if obj is None:
            raise TypeError("Argument 'obj' nie może być None.")

        from core.mixins import user_can_access_patient
        user = request.user if hasattr(request, 'user') else None
        return user_can_access_patient(user, obj)


class IsVisitParticipant(permissions.BasePermission):
    """Uprawnienie sprawdzające dostęp do wizyty."""

    def has_object_permission(self, request: object, view: object, obj: object) -> bool:
        """Sprawdza, czy użytkownik jest uczestnikiem lub ma dostęp do wizyty.

        Args:
            request (object): Obiekt żądania HTTP.
            view (object): Widok DRF.
            obj (object): Obiekt wizyty.

        Returns:
            bool: True, jeśli użytkownik posiada dostęp do wizyty.

        Raises:
            TypeError: Gdy request lub obj jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")
        if obj is None:
            raise TypeError("Argument 'obj' nie może być None.")

        from core.mixins import user_can_access_visit
        user = request.user if hasattr(request, 'user') else None
        return user_can_access_visit(user, obj)


class IsEpisodeParticipant(permissions.BasePermission):
    """Uprawnienie sprawdzające dostęp do epizodu leczenia."""

    def has_object_permission(self, request: object, view: object, obj: object) -> bool:
        """Sprawdza, czy użytkownik ma dostęp do danego epizodu leczenia.

        Args:
            request (object): Obiekt żądania HTTP.
            view (object): Widok DRF.
            obj (object): Obiekt epizodu leczenia.

        Returns:
            bool: True, jeśli użytkownik posiada dostęp do epizodu leczenia.

        Raises:
            TypeError: Gdy request lub obj jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")
        if obj is None:
            raise TypeError("Argument 'obj' nie może być None.")

        from core.mixins import user_can_access_episode
        user = request.user if hasattr(request, 'user') else None
        return user_can_access_episode(user, obj)

