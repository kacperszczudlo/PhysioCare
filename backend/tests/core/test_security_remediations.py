"""Testy weryfikujące wdrożenie remediacji bezpieczeństwa i wydajności."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from core.throttling import (
    DocumentUploadRateThrottle,
    ExportRateThrottle,
    VisitBookingRateThrottle,
)
from documents.models import MedicalDocument
from documents.views import TherapistDocumentUploadView
from patients.models import PatientProfile
from patients.views import MeDataExportView
from scheduling.models import TherapyType
from scheduling.serializers import PatientVisitRequestSerializer
from scheduling.views import MeVisitListCreateView
from therapists.models import TherapistProfile

User = get_user_model()


@pytest.mark.django_db
class TestSecurityRemediations:
    """Zestaw testów sprawdzających zabezpieczenia CSP, BFLA oraz throttling."""

    def test_document_download_includes_sandbox_csp(
        self,
        api_client: APIClient,
        patient: PatientProfile,
        tmp_path,
        settings,
    ) -> None:
        """Weryfikacja nagłówka Content-Security-Policy: sandbox przy pobieraniu plików medycznych."""
        settings.MEDIA_ROOT = tmp_path
        file_path = tmp_path / 'test_doc.pdf'
        file_path.write_bytes(b'%PDF-1.4 test content')

        doc = MedicalDocument.objects.create(
            patient=patient,
            uploaded_by=patient.user,
            title='Wyniki badań',
            file_url='/media/test_doc.pdf',
            mime_type='application/pdf',
        )

        api_client.force_authenticate(user=patient.user)
        from django.urls import reverse
        url = reverse('document-download', kwargs={'pk': doc.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.headers.get('Content-Security-Policy') == "sandbox; default-src 'none'"
        assert response.headers.get('X-Content-Type-Options') == 'nosniff'

    def test_booking_rejected_for_inactive_therapist(
        self,
        therapist: TherapistProfile,
        therapy_type: TherapyType,
    ) -> None:
        """Weryfikacja blokady rezerwacji wizyty u terapeuty z zablokowanym kontem."""
        # Blokujemy konto terapeuty
        therapist.user.is_active = False
        therapist.user.save(update_fields=['is_active'])

        start = timezone.now() + timedelta(days=2)
        end = start + timedelta(minutes=45)

        data = {
            'therapist_id': str(therapist.id),
            'therapy_type_id': str(therapy_type.id),
            'start_at': start.isoformat(),
            'end_at': end.isoformat(),
            'patient_note': 'Konsultacja',
        }

        serializer = PatientVisitRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'therapist_id' in serializer.errors
        assert any(
            'nieaktywne' in str(err).lower()
            for err in serializer.errors['therapist_id']
        )

    def test_throttling_classes_configured_on_sensitive_views(self) -> None:
        """Weryfikacja przypisania dedykowanych limiterów zapytań."""
        assert ExportRateThrottle in MeDataExportView.throttle_classes
        assert DocumentUploadRateThrottle in TherapistDocumentUploadView.throttle_classes

        # MeVisitListCreateView aplikuje VisitBookingRateThrottle dla POST
        view = MeVisitListCreateView()
        from django.test import RequestFactory
        factory = RequestFactory()

        post_req = factory.post('/api/v1/scheduling/me/visits/')
        view.request = post_req
        throttles = view.get_throttles()
        assert any(isinstance(t, VisitBookingRateThrottle) for t in throttles)

        get_req = factory.get('/api/v1/scheduling/me/visits/')
        view.request = get_req
        throttles_get = view.get_throttles()
        assert not any(isinstance(t, VisitBookingRateThrottle) for t in throttles_get)
