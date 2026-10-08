"""Zestaw testów jednostkowych i integracyjnych dla modułu administracyjnego PhysioCare.

Weryfikuje autoryzację i uprawnienia (BFLA/RBAC), endpointy analityczne dashboardu,
zarządzanie użytkownikami (blokowanie, soft delete RODO, reset hasła),
harmonogramy zbiorcze, personel fizjoterapeutyczny oraz moderację recenzji.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from patients.models import PatientProfile
from reviews.models import Review
from scheduling.models import TherapistAvailabilitySlot, TherapyType, Visit, VisitStatus
from therapists.models import TherapistProfile

User = get_user_model()


@pytest.mark.django_db
class TestAdminPermissions:
    """Weryfikacja ochrony endpointów administracyjnych przed nieuprawnionym dostępem (BFLA)."""

    def test_unauthenticated_access_returns_401(self, api_client: APIClient):
        response = api_client.get('/api/v1/admin/analytics/dashboard/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_patient_access_returns_403(self, api_client: APIClient, patient: PatientProfile):
        api_client.force_authenticate(user=patient.user)
        response = api_client.get('/api/v1/admin/analytics/dashboard/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_therapist_access_returns_403(self, api_client: APIClient, therapist: TherapistProfile):
        api_client.force_authenticate(user=therapist.user)
        response = api_client.get('/api/v1/admin/analytics/dashboard/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_access_allowed(self, api_client: APIClient, admin_user: User):
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/v1/admin/analytics/dashboard/')
        assert response.status_code == status.HTTP_200_OK

        # Weryfikacja alternatywnego aliasu URL
        response_alias = api_client.get('/api/v1/admin/dashboard/')
        assert response_alias.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestAdminDashboardAnalytics:
    """Testy agregacji i wskaźników KPI w pulpicie administratora."""

    def test_dashboard_metrics_calculation(
        self,
        api_client: APIClient,
        admin_user: User,
        therapist: TherapistProfile,
        patient: PatientProfile,
        therapy_type: TherapyType,
    ):
        now = timezone.now()
        # Utwórz 2 wizyty (jedna COMPLETED, jedna NO_SHOW)
        Visit.objects.create(
            patient=patient,
            therapist=therapist,
            therapy_type=therapy_type,
            start_at=now - timedelta(hours=2),
            end_at=now - timedelta(hours=1),
            status=VisitStatus.COMPLETED,
        )
        Visit.objects.create(
            patient=patient,
            therapist=therapist,
            therapy_type=therapy_type,
            start_at=now + timedelta(hours=1),
            end_at=now + timedelta(hours=2),
            status=VisitStatus.SCHEDULED,
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/v1/admin/analytics/dashboard/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data['users']['total'] >= 3  # admin, therapist, patient
        assert data['users']['patients_count'] >= 1
        assert data['users']['therapists_count'] >= 1
        assert data['users']['admins_count'] >= 1

        assert data['visits']['total'] >= 2
        assert data['visits']['completed'] >= 1
        assert data['visits']['scheduled'] >= 1
        assert 'show_up_rate_percent' in data['visits']
        assert 'quality' in data
        assert 'exercises' in data


@pytest.mark.django_db
class TestAdminUserManagement:
    """Testy zarządzania użytkownikami: lista, filtry, szczegóły, blokowanie i soft-delete."""

    def test_users_list_and_filtering(
        self,
        api_client: APIClient,
        admin_user: User,
        patient: PatientProfile,
        therapist: TherapistProfile,
    ):
        api_client.force_authenticate(user=admin_user)

        # Pobranie wszystkich
        res_all = api_client.get('/api/v1/admin/users/')
        assert res_all.status_code == status.HTTP_200_OK
        results = res_all.json()['results']
        assert len(results) >= 3

        # Filtr roli PATIENT
        res_patients = api_client.get('/api/v1/admin/users/?role=PATIENT')
        assert res_patients.status_code == status.HTTP_200_OK
        for u in res_patients.json()['results']:
            assert u['role'] == 'PATIENT'

        # Filtr wyszukiwania
        res_search = api_client.get(f'/api/v1/admin/users/?search={patient.user.email}')
        assert res_search.status_code == status.HTTP_200_OK
        assert len(res_search.json()['results']) == 1
        assert res_search.json()['results'][0]['id'] == str(patient.user.id)

    def test_user_detail(
        self,
        api_client: APIClient,
        admin_user: User,
        patient: PatientProfile,
        therapist: TherapistProfile,
    ):
        api_client.force_authenticate(user=admin_user)

        # Szczegóły pacjenta
        res_pt = api_client.get(f'/api/v1/admin/users/{patient.user.id}/')
        assert res_pt.status_code == status.HTTP_200_OK
        pt_data = res_pt.json()
        assert pt_data['email'] == patient.user.email
        assert pt_data['role'] == 'PATIENT'
        assert pt_data['profile_info'] is not None

        # Szczegóły terapeuty
        res_th = api_client.get(f'/api/v1/admin/users/{therapist.user.id}/')
        assert res_th.status_code == status.HTTP_200_OK
        th_data = res_th.json()
        assert th_data['role'] == 'THERAPIST'
        assert th_data['profile_info']['pwzf_number'] == therapist.pwzf_number

    def test_toggle_user_status(
        self,
        api_client: APIClient,
        admin_user: User,
        patient: PatientProfile,
    ):
        api_client.force_authenticate(user=admin_user)

        # Zablokowanie konta
        patch_res = api_client.patch(
            f'/api/v1/admin/users/{patient.user.id}/status/',
            {'is_active': False},
            format='json',
        )
        assert patch_res.status_code == status.HTTP_200_OK
        assert patch_res.json()['is_active'] is False

        patient.user.refresh_from_db()
        assert patient.user.is_active is False

        # Odblokowanie konta
        patch_res_unblock = api_client.patch(
            f'/api/v1/admin/users/{patient.user.id}/status/',
            {'is_active': True},
            format='json',
        )
        assert patch_res_unblock.status_code == status.HTTP_200_OK
        assert patch_res_unblock.json()['is_active'] is True

        patient.user.refresh_from_db()
        assert patient.user.is_active is True

    def test_cannot_deactivate_or_delete_self(
        self,
        api_client: APIClient,
        admin_user: User,
    ):
        api_client.force_authenticate(user=admin_user)

        # Próba dezaktywacji własnego konta
        res_patch = api_client.patch(
            f'/api/v1/admin/users/{admin_user.id}/status/',
            {'is_active': False},
            format='json',
        )
        assert res_patch.status_code == status.HTTP_403_FORBIDDEN

        # Próba usunięcia własnego konta
        res_del = api_client.delete(f'/api/v1/admin/users/{admin_user.id}/')
        assert res_del.status_code == status.HTTP_403_FORBIDDEN

    def test_soft_delete_user(
        self,
        api_client: APIClient,
        admin_user: User,
        patient: PatientProfile,
    ):
        api_client.force_authenticate(user=admin_user)

        res_del = api_client.delete(f'/api/v1/admin/users/{patient.user.id}/')
        assert res_del.status_code == status.HTTP_200_OK

        patient.user.refresh_from_db()
        assert patient.user.is_active is False

    @patch('administration.views.send_password_reset_code', return_value=True)
    def test_admin_reset_password_trigger(
        self,
        mock_send_reset,
        api_client: APIClient,
        admin_user: User,
        patient: PatientProfile,
    ):
        api_client.force_authenticate(user=admin_user)

        res = api_client.post(f'/api/v1/admin/users/{patient.user.id}/reset-password/')
        assert res.status_code == status.HTTP_200_OK
        assert mock_send_reset.called


@pytest.mark.django_db
class TestAdminSchedulingAndReviews:
    """Testy zbiorczego kalendarza oraz moderacji opinii."""

    def test_scheduling_overview(
        self,
        api_client: APIClient,
        admin_user: User,
        therapist: TherapistProfile,
        patient: PatientProfile,
        therapy_type: TherapyType,
    ):
        now = timezone.now()
        Visit.objects.create(
            patient=patient,
            therapist=therapist,
            therapy_type=therapy_type,
            start_at=now + timedelta(hours=1),
            end_at=now + timedelta(hours=2),
            status=VisitStatus.SCHEDULED,
        )
        TherapistAvailabilitySlot.objects.create(
            therapist=therapist,
            day_of_week=0,
            start_time='08:00',
            end_time='16:00',
            is_recurring=True,
            is_active=True,
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/v1/admin/scheduling/overview/')
        assert response.status_code == status.HTTP_200_OK

        # Weryfikacja alternatywnego aliasu URL
        response_alias = api_client.get('/api/v1/admin/schedules/overview/')
        assert response_alias.status_code == status.HTTP_200_OK
        data = response.json()

        assert 'range' in data
        assert len(data['therapists']) >= 1
        assert len(data['visits']) >= 1
        assert len(data['availability_slots']) >= 1

    def test_therapist_stats(
        self,
        api_client: APIClient,
        admin_user: User,
        therapist: TherapistProfile,
        patient: PatientProfile,
        therapy_type: TherapyType,
    ):
        now = timezone.now()
        Visit.objects.create(
            patient=patient,
            therapist=therapist,
            therapy_type=therapy_type,
            start_at=now - timedelta(hours=3),
            end_at=now - timedelta(hours=2),
            status=VisitStatus.COMPLETED,
        )

        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/v1/admin/therapists/stats/')
        assert response.status_code == status.HTTP_200_OK
        stats_list = response.json()
        assert len(stats_list) >= 1

        th_stat = next(s for s in stats_list if s['therapist_id'] == str(therapist.id))
        assert th_stat['completed_visits'] >= 1
        assert th_stat['pwzf_number'] == therapist.pwzf_number

    def test_reviews_list_and_visibility_toggle(
        self,
        api_client: APIClient,
        admin_user: User,
        therapist: TherapistProfile,
        patient: PatientProfile,
        therapy_type: TherapyType,
    ):
        now = timezone.now()
        visit = Visit.objects.create(
            patient=patient,
            therapist=therapist,
            therapy_type=therapy_type,
            start_at=now - timedelta(days=1),
            end_at=now - timedelta(days=1, hours=-1),
            status=VisitStatus.COMPLETED,
        )
        review = Review.objects.create(
            patient=patient,
            therapist=therapist,
            visit=visit,
            rating=5,
            comment='Wspaniały fizjoterapeuta!',
            is_visible=True,
        )

        api_client.force_authenticate(user=admin_user)

        # Lista opinii
        res_list = api_client.get('/api/v1/admin/reviews/')
        assert res_list.status_code == status.HTTP_200_OK
        assert len(res_list.json()['results']) >= 1

        # Ukrycie opinii
        res_hide = api_client.patch(
            f'/api/v1/admin/reviews/{review.id}/visibility/',
            {'is_visible': False},
            format='json',
        )
        assert res_hide.status_code == status.HTTP_200_OK
        assert res_hide.json()['is_visible'] is False

        review.refresh_from_db()
        assert review.is_visible is False

        therapist.refresh_from_db()
        assert therapist.rating_count == 0  # Ukryta opinia nie liczy się do średniej!

    def test_admin_profile_me_get_and_patch(
        self,
        api_client: APIClient,
        admin_user: User,
    ):
        api_client.force_authenticate(user=admin_user)

        res_get = api_client.get('/api/v1/auth/me/')
        assert res_get.status_code == status.HTTP_200_OK
        data = res_get.json()
        assert data['user']['email'] == admin_user.email
        assert data['user']['role'] == 'ADMIN'

        res_patch = api_client.patch(
            '/api/v1/auth/me/',
            {'first_name': 'Kacper Nowy', 'last_name': 'Admin Nowy'},
            format='json',
        )
        assert res_patch.status_code == status.HTTP_200_OK
        assert res_patch.json()['user']['first_name'] == 'Kacper Nowy'
        assert res_patch.json()['user']['last_name'] == 'Admin Nowy'

        admin_user.refresh_from_db()
        assert admin_user.first_name == 'Kacper Nowy'
        assert admin_user.last_name == 'Admin Nowy'

