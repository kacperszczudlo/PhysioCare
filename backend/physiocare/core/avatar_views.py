from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import parsers, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsPatient, IsTherapist
from core.storage import save_avatar
from patients.serializers import MeProfileSerializer
from therapists.serializers import TherapistProfileSerializer


def _upload_avatar_for_profile(request: object, profile: object, *, response_serializer: object) -> Response:
    """Zapisuje przesłany plik awatara dla profilu użytkownika.

    Args:
        request (object): Obiekt żądania HTTP DRF z przesłanym plikiem.
        profile (object): Obiekt profilu pacjenta lub terapeuty.
        response_serializer (object): Klasa serializatora profilu do zwrócenia odpowiedzi.

    Returns:
        Response: Obiekt odpowiedzi Response DRF z zaktualizowanymi danymi profilu lub błędem.

    Raises:
        ValidationError: Gdy plik awatara nie przejdzie walidacji.
        TypeError: Gdy któryś z wymaganych argumentów jest None.
    """
    if request is None:
        raise TypeError("Argument 'request' nie może być None.")
    if profile is None:
        raise TypeError("Argument 'profile' nie może być None.")
    if response_serializer is None:
        raise TypeError("Argument 'response_serializer' nie może być None.")

    files = request.FILES if hasattr(request, 'FILES') else {}
    uploaded = files.get('file')
    if uploaded is None:
        return Response(
            {
                'error': {
                    'code': 'FILE_REQUIRED',
                    'message': 'Wymagany plik zdjęcia (JPEG, PNG lub WebP).',
                    'details': {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        prev_url = profile.avatar_url if hasattr(profile, 'avatar_url') else ''
        profile.avatar_url = save_avatar(uploaded, previous_url=prev_url or '')
    except DjangoValidationError as exc:
        messages = list(exc.messages) if hasattr(exc, 'messages') else [str(exc)]
        raise ValidationError({'file': messages}) from exc

    if hasattr(profile, 'save'):
        profile.save(update_fields=['avatar_url'])
    return Response(response_serializer(profile).data, status=status.HTTP_200_OK)


class TherapistAvatarUploadView(APIView):
    """Widok służący do wgrywania zdjęcia profilowego przez terapeutę."""

    permission_classes = [IsAuthenticated, IsTherapist]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request: object) -> Response:
        """Przetwarza żądanie przesłania pliku awatara terapeuty.

        Args:
            request (object): Obiekt żądania HTTP.

        Returns:
            Response: Odpowiedź HTTP z danymi profilu terapeuty po aktualizacji awatara.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        user = request.user if hasattr(request, 'user') else None
        therapist_profile = user.therapist_profile if hasattr(user, 'therapist_profile') else None
        return _upload_avatar_for_profile(
            request,
            therapist_profile,
            response_serializer=TherapistProfileSerializer,
        )


class MeAvatarUploadView(APIView):
    """Widok służący do wgrywania zdjęcia profilowego przez zalogowanego pacjenta."""

    permission_classes = [IsAuthenticated, IsPatient]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request: object) -> Response:
        """Przetwarza żądanie przesłania pliku awatara pacjenta.

        Args:
            request (object): Obiekt żądania HTTP.

        Returns:
            Response: Odpowiedź HTTP z danymi profilu pacjenta po aktualizacji awatara.

        Raises:
            TypeError: Gdy request jest None.
        """
        if request is None:
            raise TypeError("Argument 'request' nie może być None.")

        user = request.user if hasattr(request, 'user') else None
        patient_profile = user.patient_profile if hasattr(user, 'patient_profile') else None
        return _upload_avatar_for_profile(
            request,
            patient_profile,
            response_serializer=MeProfileSerializer,
        )

