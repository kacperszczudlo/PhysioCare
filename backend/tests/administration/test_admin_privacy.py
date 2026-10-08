"""Zestaw testów dla endpointów RODO i zarządzania prywatnością w panelu administratora."""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from patients.models import PatientProfile
from privacy.models import AccountDeletionRequest, Consent, ConsentType
from therapists.models import TherapistProfile

User = get_user_model()


@pytest.mark.django_db
class TestAdminPrivacyAccess:
    """Weryfikacja uprawnień dostępu do endpointów RODO."""

    def test_unauthenticated_access_denied(self, api_client: APIClient) -> None:
        """Sprawdza, czy nieuwierzytelniony użytkownik otrzymuje kod 401."""
        res = api_client.get('/api/v1/admin/privacy/requests/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

        res_consents = api_client.get('/api/v1/admin/privacy/consents/')
        assert res_consents.status_code == status.HTTP_401_UNAUTHORIZED

    def test_patient_forbidden(self, api_client: APIClient, patient: PatientProfile) -> None:
        """Sprawdza, czy pacjent nie ma uprawnień do endpointów administracyjnych RODO (403)."""
        api_client.force_authenticate(user=patient.user)
        res = api_client.get('/api/v1/admin/privacy/requests/')
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_therapist_forbidden(self, api_client: APIClient, therapist: TherapistProfile) -> None:
        """Sprawdza, czy fizjoterapeuta nie ma uprawnień do endpointów administracyjnych RODO (403)."""
        api_client.force_authenticate(user=therapist.user)
        res = api_client.get('/api/v1/admin/privacy/requests/')
        assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAdminPrivacyRequests:
    """Weryfikacja obsługi wniosków o usunięcie konta przez administratora."""

    def test_list_and_filter_requests(
        self,
        api_client: APIClient,
        admin_user: User,
        patient: PatientProfile,
    ) -> None:
        """Weryfikuje listowanie oraz filtrowanie wniosków o usunięcie konta po statusie przetworzenia."""
        api_client.force_authenticate(user=admin_user)

        user2 = User.objects.create_user(
            email='patient2_test@example.com',
            password='TestPassword123!',
            first_name='Jan',
            last_name='Kowalski',
        )

        req1 = AccountDeletionRequest.objects.create(
            user=patient.user,
            reason='Rezygnacja z usług',
            processed_at=None,
        )
        req2 = AccountDeletionRequest.objects.create(
            user=user2,
            reason='Brak potrzeby',
            processed_at=timezone.now(),
        )

        res = api_client.get('/api/v1/admin/privacy/requests/')
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data)
        assert len(results) >= 2

        # Filtr oczekujących
        res_pending = api_client.get('/api/v1/admin/privacy/requests/?is_processed=false')
        results_pending = res_pending.data.get('results', res_pending.data)
        assert any(r['id'] == str(req1.id) for r in results_pending)
        assert not any(r['id'] == str(req2.id) for r in results_pending)

        # Filtr zrealizowanych
        res_processed = api_client.get('/api/v1/admin/privacy/requests/?is_processed=true')
        results_processed = res_processed.data.get('results', res_processed.data)
        assert any(r['id'] == str(req2.id) for r in results_processed)
        assert not any(r['id'] == str(req1.id) for r in results_processed)

    def test_process_deletion_request_anonymizes_user(
        self,
        api_client: APIClient,
        admin_user: User,
        patient: PatientProfile,
    ) -> None:
        """Weryfikuje, że zatwierdzenie wniosku przez administratora wykonuje pełną anonimizację RODO."""
        api_client.force_authenticate(user=admin_user)

        req = AccountDeletionRequest.objects.create(
            user=patient.user,
            reason='Chcę skasować profil',
            processed_at=None,
        )

        res = api_client.post(
            f'/api/v1/admin/privacy/requests/{req.id}/process/',
            {'notes': 'Zatwierdzono telefonicznie'},
            format='json',
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.data['is_processed'] is True

        req.refresh_from_db()
        assert req.processed_at is not None
        assert '[Admin note: Zatwierdzono telefonicznie]' in req.notes

        patient.user.refresh_from_db()
        assert patient.user.is_active is False
        assert patient.user.email.startswith('deleted-')
        assert patient.user.first_name == 'Usunięte'

    def test_process_deletion_request_protects_superuser(
        self,
        api_client: APIClient,
    ) -> None:
        """Weryfikuje, że zwykły administrator nie może przetworzyć wniosku usunięcia superusera."""
        staff_admin = User.objects.create_user(
            email='staff_admin@physiocare.test',
            password='TestPassword123!',
            role='ADMIN',
            is_staff=True,
            is_superuser=False,
            email_verified_at=timezone.now(),
        )
        api_client.force_authenticate(user=staff_admin)

        root = User.objects.create_superuser(
            email='root_target@example.com',
            password='RootPassword123!',
        )
        req = AccountDeletionRequest.objects.create(
            user=root,
            reason='Superuser delete test',
            processed_at=None,
        )

        res = api_client.post(
            f'/api/v1/admin/privacy/requests/{req.id}/process/',
            {'notes': 'Próba usunięcia roota'},
            format='json',
        )
        assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAdminPrivacyConsents:
    """Weryfikacja przeglądania rejestru zgód RODO."""

    def test_list_and_filter_consents(
        self,
        api_client: APIClient,
        admin_user: User,
        patient: PatientProfile,
    ) -> None:
        """Weryfikuje pobieranie i filtrowanie zgód po typie oraz fladze udzielenia."""
        api_client.force_authenticate(user=admin_user)

        c1 = Consent.objects.create(
            user=patient.user,
            consent_type=ConsentType.TERMS_REQUIRED,
            granted=True,
        )
        c2 = Consent.objects.create(
            user=admin_user,
            consent_type=ConsentType.MARKETING_OPTIONAL,
            granted=False,
        )

        res = api_client.get('/api/v1/admin/privacy/consents/')
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data)
        assert len(results) >= 2

        # Filtr consent_type
        res_marketing = api_client.get(
            f'/api/v1/admin/privacy/consents/?consent_type={ConsentType.MARKETING_OPTIONAL}'
        )
        results_marketing = res_marketing.data.get('results', res_marketing.data)
        assert any(r['id'] == str(c2.id) for r in results_marketing)
        assert not any(r['id'] == str(c1.id) for r in results_marketing)

        # Filtr granted
        res_granted = api_client.get('/api/v1/admin/privacy/consents/?granted=true')
        results_granted = res_granted.data.get('results', res_granted.data)
        assert any(r['id'] == str(c1.id) for r in results_granted)
        assert not any(r['id'] == str(c2.id) for r in results_granted)
