"""Authenticated media serving - never expose PHI files anonymously."""

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
    normalized = relative.replace('\\', '/').lstrip('/')
    return f'/media/{normalized}'


def user_can_access_exercise_file(user, exercise) -> bool:
    if user.role == 'THERAPIST':
        return (
            hasattr(user, 'therapist_profile')
            and exercise.therapist_id == user.therapist_profile.id
        )
    if user.role == 'PATIENT':
        if not hasattr(user, 'patient_profile'):
            return False
        from exercises.models import ExerciseAssignment

        return ExerciseAssignment.objects.filter(
            exercise=exercise,
            patient=user.patient_profile,
        ).exists()
    return bool(user.is_staff)


def user_can_access_avatar(user, media_url: str) -> bool:
    """Avatar only for owner, linked therapist↔patient, or staff."""
    if user.is_staff:
        return True

    from patients.models import PatientProfile
    from therapists.models import TherapistProfile

    patient = PatientProfile.objects.filter(avatar_url=media_url).first()
    if patient is not None:
        return user_can_access_patient(user, patient)

    therapist = TherapistProfile.objects.filter(avatar_url=media_url).first()
    if therapist is None:
        return False

    if user.role == 'THERAPIST':
        return (
            hasattr(user, 'therapist_profile')
            and user.therapist_profile.id == therapist.id
        )
    if user.role == 'PATIENT':
        from core.mixins import patient_belongs_to_therapist

        return (
            hasattr(user, 'patient_profile')
            and patient_belongs_to_therapist(user.patient_profile, therapist)
        )
    return False


def user_may_access_media_path(user, relative: str) -> bool:
    """Authorize by media subfolder and owning record."""
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
    """Serve files from MEDIA_ROOT only after JWT cookie/Bearer auth + ownership."""

    permission_classes = [IsAuthenticated]

    def get(self, request, path: str):
        relative = path.replace('\\', '/').lstrip('/')
        if not relative or '..' in relative.split('/'):
            raise Http404

        try:
            absolute = safe_join(str(settings.MEDIA_ROOT), relative)
        except ValueError as exc:
            raise Http404 from exc

        if not absolute or not os.path.isfile(absolute):
            raise Http404

        if not user_may_access_media_path(request.user, relative):
            raise Http404

        content_type, _encoding = mimetypes.guess_type(absolute)
        # FileResponse closes the file handle after the response is sent.
        response = FileResponse(
            open(absolute, 'rb'),  # noqa: SIM115
            content_type=content_type or 'application/octet-stream',
        )
        response['X-Content-Type-Options'] = 'nosniff'
        response['Cache-Control'] = 'private, no-store'
        return response
