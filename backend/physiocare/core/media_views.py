from __future__ import annotations

import mimetypes
import os

from django.conf import settings
from django.http import FileResponse, Http404
from django.utils._os import safe_join
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.mixins import user_can_access_patient


def _media_url_from_relative(relative: str) -> str:
    """Tworzy bezwzględną ścieżkę mediów `/media/...` z względnej ścieżki pliku.

    Args:
        relative (str): Względna ścieżka do pliku.

    Returns:
        str: Adres URL zasobu mediów.

    Raises:
        TypeError: Gdy relative nie jest napisem.
    """
    if not isinstance(relative, str):
        raise TypeError("Argument 'relative' musi być typu str.")

    normalized = relative.replace('\\', '/').lstrip('/')
    return f'/media/{normalized}'


def user_can_access_exercise_file(user: object, exercise: object) -> bool:
    """Sprawdza uprawnienia użytkownika do pobrania pliku ćwiczenia.

    Args:
        user (object): Obiekt uwierzytelnionego użytkownika.
        exercise (object): Obiekt modelu ćwiczenia.

    Returns:
        bool: True jeśli użytkownik posiada dostęp, False w przeciwnym razie.

    Raises:
        TypeError: Gdy user lub exercise jest None.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")
    if exercise is None:
        raise TypeError("Argument 'exercise' nie może być None.")

    user_role = user.role if hasattr(user, 'role') else ''
    if user_role == 'THERAPIST':
        therapist_profile = user.therapist_profile if hasattr(user, 'therapist_profile') else None
        exercise_therapist_id = exercise.therapist_id if hasattr(exercise, 'therapist_id') else None
        return (
            therapist_profile is not None
            and exercise_therapist_id == therapist_profile.id
        )
    if user_role == 'PATIENT':
        if not hasattr(user, 'patient_profile'):
            return False
        from exercises.models import ExerciseAssignment

        return ExerciseAssignment.objects.filter(
            exercise=exercise,
            patient=user.patient_profile,
        ).exists()
    return bool(hasattr(user, 'is_staff') and user.is_staff)


def user_can_access_avatar(user: object, media_url: str) -> bool:
    """Sprawdza uprawnienia dostępu do pliku awatara profilu.

    Args:
        user (object): Obiekt użytkownika.
        media_url (str): Adres URL awatara.

    Returns:
        bool: True jeśli dostęp jest dozwolony, False w przeciwnym razie.

    Raises:
        TypeError: Gdy user jest None lub media_url nie jest napisem.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")
    if not isinstance(media_url, str):
        raise TypeError("Argument 'media_url' musi być typu str.")

    if hasattr(user, 'is_staff') and user.is_staff:
        return True

    from patients.models import PatientProfile
    from therapists.models import TherapistProfile

    patient = PatientProfile.objects.filter(avatar_url=media_url).first()
    if patient is not None:
        return user_can_access_patient(user, patient)

    therapist = TherapistProfile.objects.filter(avatar_url=media_url).first()
    if therapist is None:
        return False

    user_role = user.role if hasattr(user, 'role') else ''
    if user_role == 'THERAPIST':
        therapist_profile = user.therapist_profile if hasattr(user, 'therapist_profile') else None
        return (
            therapist_profile is not None
            and therapist_profile.id == therapist.id
        )
    if user_role == 'PATIENT':
        from core.mixins import patient_belongs_to_therapist

        patient_profile = user.patient_profile if hasattr(user, 'patient_profile') else None
        return (
            patient_profile is not None
            and patient_belongs_to_therapist(patient_profile, therapist)
        )
    return False


def user_may_access_media_path(user: object, relative: str) -> bool:
    """Weryfikuje uprawnienia użytkownika do pliku w podkatalogu mediów.

    Args:
        user (object): Obiekt użytkownika.
        relative (str): Względna ścieżka do pliku.

    Returns:
        bool: True jeśli dostęp do ścieżki jest autoryzowany.

    Raises:
        TypeError: Gdy user jest None lub relative nie jest napisem.
    """
    if user is None:
        raise TypeError("Argument 'user' nie może być None.")
    if not isinstance(relative, str):
        raise TypeError("Argument 'relative' musi być typu str.")

    normalized = relative.replace('\\', '/').lstrip('/')
    if not normalized or normalized.startswith('../') or '/../' in normalized:
        return False

    subdir, _, _rest = normalized.partition('/')
    media_url = _media_url_from_relative(normalized)

    if subdir == 'avatars':
        return user_can_access_avatar(user, media_url)

    if subdir == 'documents':
        from documents.models import MedicalDocument

        document = (
            MedicalDocument.objects.select_related('patient')
            .filter(file_url=media_url)
            .first()
        )
        if document is None:
            return False
        return user_can_access_patient(user, document.patient)

    if subdir == 'exercises':
        from exercises.models import Exercise

        exercise = Exercise.objects.filter(file_url=media_url).first()
        if exercise is None:
            return False
        return user_can_access_exercise_file(user, exercise)

    return False


class ProtectedMediaServeView(APIView):
    """Widok bezpiecznego serwowania plików mediów z autoryzacją i weryfikacją uprawnień dostępu."""

    permission_classes = [IsAuthenticated]

    def get(self, request: object, path: str) -> FileResponse:
        """Obsługuje żądanie pobrania pliku z chronionego katalogu mediów.

        Args:
            request (object): Obiekt żądania HTTP.
            path (str): Względna ścieżka pliku mediów.

        Returns:
            FileResponse: Odpowiedź ze strumieniem pliku.

        Raises:
            Http404: Gdy plik nie istnieje lub użytkownik nie posiada do niego uprawnień.
            TypeError: Gdy request jest None lub path nie jest napisem.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")
        if not isinstance(path, str):
            raise TypeError("Argument 'path' musi być typu str.")

        relative = path.replace('\\', '/').lstrip('/')
        if not relative or '..' in relative.split('/'):
            raise Http404

        try:
            absolute = safe_join(str(settings.MEDIA_ROOT), relative)
        except ValueError as exc:
            raise Http404 from exc

        if not absolute or not os.path.isfile(absolute):
            raise Http404

        user = request.user if hasattr(request, 'user') else None
        if not user_may_access_media_path(user, relative):
            raise Http404

        content_type, _encoding = mimetypes.guess_type(absolute)
        response = FileResponse(
            open(absolute, 'rb'),  # noqa: SIM115
            content_type=content_type or 'application/octet-stream',
        )
        response['X-Content-Type-Options'] = 'nosniff'
        response['Cache-Control'] = 'private, no-store'
        return response

