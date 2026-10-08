import os

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import QuerySet
from django.http import FileResponse, Http404
from django.utils._os import safe_join
from rest_framework import generics, parsers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
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
from core.throttling import DocumentUploadRateThrottle
from notifications.events import notify_new_document
from scheduling.models import Visit
from treatment.models import TreatmentEpisode

from .models import MedicalDocument
from .serializers import MedicalDocumentSerializer


class MeDocumentsListView(PatientSelfMixin, generics.ListAPIView):
    """Widok listy dokumentów medycznych należących do zalogowanego pacjenta."""

    serializer_class = MedicalDocumentSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self) -> QuerySet[MedicalDocument]:
        """Pobiera listę dokumentów medycznych dla zalogowanego pacjenta.

        Returns:
            QuerySet[MedicalDocument]: Queryset dokumentów medycznych posortowanych od najnowszych.
        """
        return MedicalDocument.objects.filter(
            patient=self.get_patient_profile(),
        ).order_by('-created_at')


class TherapistDocumentUploadView(generics.CreateAPIView):
    """Widok umożliwiający terapeucie wgrywanie dokumentów medycznych dla pacjenta."""

    serializer_class = MedicalDocumentSerializer
    permission_classes = [IsAuthenticated, IsTherapist]
    throttle_classes = [DocumentUploadRateThrottle]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        """Przetwarza przesłany plik dokumentu medycznego i przypisuje go do pacjenta.

        Args:
            request (Request): Obiekt żądania HTTP DRF.
            *args (object): Pozycyjne argumenty dodatkowe.
            **kwargs (object): Słownikowe argumenty dodatkowe.

        Returns:
            Response: Odpowiedź HTTP z utworzonym obiektem dokumentu medycznego lub błędem walidacji.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        uploaded = request.FILES.get('file')
        if uploaded is None:
            return Response(
                {'error': {'code': 'FILE_REQUIRED', 'message': 'Wymagany plik.', 'details': {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        patient_id = request.data.get('patient_id')
        from patients.models import PatientProfile

        patient = (
            PatientProfile.objects.filter(
                therapist_links__therapist=request.user.therapist_profile,
                therapist_links__status='ACTIVE',
                user__is_active=True,
                pk=patient_id,
            ).first()
        )
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

        file_url, sniffed = save_upload(uploaded, subdir='documents')
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
            mime_type=sniffed,
            visit_id=visit_id,
            episode_id=episode_id,
        )
        notify_new_document(document)
        return Response(MedicalDocumentSerializer(document).data, status=status.HTTP_201_CREATED)


class DocumentDownloadView(APIView):
    """Widok pobierania pliku dokumentu medycznego."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, pk: object, *args: object, **kwargs: object) -> FileResponse:
        """Pobiera i serwuje plik dokumentu medycznego, sprawdzając uprawnienia użytkownika.

        Args:
            request (Request): Obiekt żądania HTTP.
            pk (object): Identyfikator dokumentu medycznego.
            *args (object): Pozycyjne argumenty dodatkowe.
            **kwargs (object): Słownikowe argumenty dodatkowe.

        Returns:
            FileResponse: Strumieniowana odpowiedź plikowa FileResponse.

        Raises:
            TypeError: Gdy parametr request nie jest instancją Request.
            Http404: Gdy dokument nie istnieje, brak uprawnień lub plik fizyczny nie został odnaleziony.
        """
        if not isinstance(request, Request):
            raise TypeError('Argument request musi być instancją Request.')

        document = MedicalDocument.objects.select_related('patient').filter(pk=pk).first()
        if document is None:
            raise Http404
        if not user_can_access_patient(request.user, document.patient):
            raise Http404

        relative = document.file_url.removeprefix('/media/').lstrip('/')
        if not relative or '..' in relative.split('/'):
            raise Http404
        try:
            path = safe_join(str(settings.MEDIA_ROOT), relative)
        except ValueError as exc:
            raise Http404 from exc
        if not path or not os.path.isfile(path):
            raise Http404
        response = FileResponse(
            open(path, 'rb'),  # noqa: SIM115
            content_type=document.mime_type,
            as_attachment=True,
        )
        response['X-Content-Type-Options'] = 'nosniff'
        response['Cache-Control'] = 'private, no-store'
        response['Content-Security-Policy'] = "sandbox; default-src 'none'"
        return response

