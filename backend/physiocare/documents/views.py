import os

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import FileResponse, Http404
from rest_framework import generics, parsers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.field_policies import (
    DOCUMENT_TITLE_REQUIRED,
    DOCUMENT_TITLE_TOO_LONG,
    normalize_optional_text,
)
from core.mixins import PatientSelfMixin, user_can_access_patient
from core.permissions import IsPatient, IsTherapist
from core.storage import save_upload
from scheduling.models import Visit
from treatment.models import TreatmentEpisode

from .models import MedicalDocument
from .serializers import MedicalDocumentSerializer


class MeDocumentsListView(PatientSelfMixin, generics.ListAPIView):
    serializer_class = MedicalDocumentSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self):
        return MedicalDocument.objects.filter(
            patient=self.get_patient_profile(),
        ).order_by('-created_at')


class TherapistDocumentUploadView(generics.CreateAPIView):
    serializer_class = MedicalDocumentSerializer
    permission_classes = [IsAuthenticated, IsTherapist]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def create(self, request, *args, **kwargs):
        uploaded = request.FILES.get('file')
        if uploaded is None:
            return Response(
                {'error': {'code': 'FILE_REQUIRED', 'message': 'Wymagany plik.', 'details': {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        patient_id = request.data.get('patient_id')
        patient = request.user.therapist_profile.patients.filter(pk=patient_id).first()
        if patient is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        raw_title = request.data.get('title', uploaded.name)
        try:
            title = normalize_optional_text(
                raw_title,
                max_length=200,
                too_long_message=DOCUMENT_TITLE_TOO_LONG,
                allow_blank=False,
                required_message=DOCUMENT_TITLE_REQUIRED,
            )
        except DjangoValidationError as exc:
            return Response(
                {
                    'error': {
                        'code': 'VALIDATION',
                        'message': exc.messages[0],
                        'details': {'title': list(exc.messages)},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_url = save_upload(uploaded, subdir='documents')
        visit_id = request.data.get('visit_id') or None
        episode_id = request.data.get('episode_id') or None

        if visit_id and not Visit.objects.filter(pk=visit_id, patient=patient).exists():
            return Response(
                {
                    'error': {
                        'code': 'VALIDATION',
                        'message': 'Wizyta nie należy do wskazanego pacjenta.',
                        'details': {'visit_id': visit_id},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if episode_id and not TreatmentEpisode.objects.filter(
            pk=episode_id, patient=patient
        ).exists():
            return Response(
                {
                    'error': {
                        'code': 'VALIDATION',
                        'message': 'Epizod nie należy do wskazanego pacjenta.',
                        'details': {'episode_id': episode_id},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        document = MedicalDocument.objects.create(
            patient=patient,
            uploaded_by=request.user,
            title=title,
            file_url=file_url,
            mime_type=getattr(uploaded, 'content_type', 'application/pdf'),
            visit_id=visit_id,
            episode_id=episode_id,
        )
        return Response(MedicalDocumentSerializer(document).data, status=status.HTTP_201_CREATED)


class DocumentDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        document = MedicalDocument.objects.select_related('patient').filter(pk=pk).first()
        if document is None:
            raise Http404
        if not user_can_access_patient(request.user, document.patient):
            raise Http404

        relative = document.file_url.removeprefix('/media/')
        path = os.path.join(str(settings.MEDIA_ROOT), relative)
        if not os.path.isfile(path):
            raise Http404
        return FileResponse(open(path, 'rb'), content_type=document.mime_type, as_attachment=True)
