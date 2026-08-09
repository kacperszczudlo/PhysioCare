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


def _upload_avatar_for_profile(request, profile, *, response_serializer):
    uploaded = request.FILES.get('file')
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
        profile.avatar_url = save_avatar(uploaded, previous_url=profile.avatar_url or '')
    except DjangoValidationError as exc:
        messages = list(exc.messages) if hasattr(exc, 'messages') else [str(exc)]
        raise ValidationError({'file': messages}) from exc

    profile.save(update_fields=['avatar_url'])
    return Response(response_serializer(profile).data, status=status.HTTP_200_OK)


class TherapistAvatarUploadView(APIView):
    permission_classes = [IsAuthenticated, IsTherapist]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        return _upload_avatar_for_profile(
            request,
            request.user.therapist_profile,
            response_serializer=TherapistProfileSerializer,
        )


class MeAvatarUploadView(APIView):
    permission_classes = [IsAuthenticated, IsPatient]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        return _upload_avatar_for_profile(
            request,
            request.user.patient_profile,
            response_serializer=MeProfileSerializer,
        )
