import pytest
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import CustomUser, RoleChoices
from patients.models import PatientProfile, PatientTherapistLink, LinkStatus
from therapists.models import TherapistProfile
from scheduling.models import TherapyType, Visit, VisitStatus
from treatment.models import TreatmentEpisode, VisitNote, DiagnosticRecommendation


@pytest.fixture
def therapist1(db):
    user = CustomUser.objects.create_user(
        email='therapist1@example.com',
        password='Password123!',
        role=RoleChoices.THERAPIST,
        first_name='Jan',
        last_name='Kowalski',
    )
    return TherapistProfile.objects.create(
        user=user,
        pwzf_number='PWZF10001',
        phone='+48600111222',
        location_address='Warszawa, ul. Prosta 1',
    )


@pytest.fixture
def therapist2(db):
    user = CustomUser.objects.create_user(
        email='therapist2@example.com',
        password='Password123!',
        role=RoleChoices.THERAPIST,
        first_name='Anna',
        last_name='Nowak',
    )
    return TherapistProfile.objects.create(
        user=user,
        pwzf_number='PWZF10002',
        phone='+48600333444',
        location_address='Kraków, ul. Długa 5',
    )


@pytest.fixture
def patient_user(db):
    user = CustomUser.objects.create_user(
        email='patient@example.com',
        password='Password123!',
        role=RoleChoices.PATIENT,
        first_name='Adam',
        last_name='Wiśniewski',
    )
    PatientProfile.objects.create(user=user, phone='+48500111222')
    return user


@pytest.mark.django_db
class TestPatientTherapistM2M:

    def test_register_patient_without_therapist(self):
        client = APIClient()
        response = client.post(
            '/api/v1/auth/register/patient/',
            {
                'email': 'newpatient@example.com',
                'password': 'Password123!',
                'first_name': 'Michał',
                'last_name': 'Zieliński',
                'consents': {'terms': True, 'medical_data': True},
            },
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        profile = PatientProfile.objects.get(user__email='newpatient@example.com')
        assert profile.therapist_links.count() == 0

    def test_register_patient_with_therapist_code(self, therapist1):
        client = APIClient()
        response = client.post(
            '/api/v1/auth/register/patient/',
            {
                'email': 'codedpatient@example.com',
                'password': 'Password123!',
                'first_name': 'Piotr',
                'last_name': 'Wójcik',
                'therapist_code': therapist1.pwzf_number,
                'consents': {'terms': True, 'medical_data': True},
            },
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        profile = PatientProfile.objects.get(user__email='codedpatient@example.com')
        assert profile.therapist_links.filter(therapist=therapist1, status=LinkStatus.ACTIVE).exists()

    def test_link_and_unlink_therapist_endpoints(self, patient_user, therapist1, therapist2):
        client = APIClient()
        client.force_authenticate(user=patient_user)

        # Initially 0 linked therapists
        res = client.get('/api/v1/me/therapists/')
        assert res.status_code == status.HTTP_200_OK
        data = res.data.get('results', res.data) if isinstance(res.data, dict) else res.data
        assert len(data) == 0

        # Link therapist1 by ID
        link_res = client.post(
            '/api/v1/me/therapists/link/',
            {'therapist_id': str(therapist1.id)},
            format='json',
        )
        assert link_res.status_code == status.HTTP_201_CREATED

        # Link therapist2 by PWZF code
        link_res2 = client.post(
            '/api/v1/me/therapists/link/',
            {'therapist_code': therapist2.pwzf_number},
            format='json',
        )
        assert link_res2.status_code == status.HTTP_201_CREATED

        # Check me therapists list
        res = client.get('/api/v1/me/therapists/')
        data = res.data.get('results', res.data) if isinstance(res.data, dict) else res.data
        assert len(data) == 2

        # Unlink therapist1
        unlink_res = client.delete(f'/api/v1/me/therapists/{therapist1.id}/')
        assert unlink_res.status_code == status.HTTP_200_OK

        res_after = client.get('/api/v1/me/therapists/')
        data_after = res_after.data.get('results', res_after.data) if isinstance(res_after.data, dict) else res_after.data
        assert len(data_after) == 1
        assert data_after[0]['id'] == str(therapist2.id)

    def test_public_therapist_search(self, patient_user, therapist1, therapist2):
        client = APIClient()
        client.force_authenticate(user=patient_user)

        res = client.get('/api/v1/therapists/public/?search=Kowalski')
        assert res.status_code == status.HTTP_200_OK
        results = res.data.get('results', res.data) if isinstance(res.data, dict) else res.data
        assert len(results) == 1
        assert results[0]['id'] == str(therapist1.id)

    def test_auto_link_on_visit_booking(self, patient_user, therapist1):
        client = APIClient()
        client.force_authenticate(user=patient_user)

        tt = TherapyType.objects.create(
            therapist=therapist1,
            name='Konsultacja fizjoterapeutyczna',
            duration_min=45,
        )

        from django.utils import timezone
        import datetime
        start = timezone.now() + datetime.timedelta(days=2)
        end = start + datetime.timedelta(minutes=45)

        # Mock availability slot (non-recurring explicit slot)
        from scheduling.models import TherapistAvailabilitySlot
        TherapistAvailabilitySlot.objects.create(
            therapist=therapist1,
            is_recurring=False,
            start_at=start - datetime.timedelta(hours=1),
            end_at=end + datetime.timedelta(hours=1),
            is_active=True,
        )

        visit_res = client.post(
            '/api/v1/me/visits/',
            {
                'therapist_id': str(therapist1.id),
                'therapy_type_id': str(tt.id),
                'start_at': start.isoformat(),
                'end_at': end.isoformat(),
                'patient_note': 'Ból kolana',
            },
            format='json',
        )
        assert visit_res.status_code == status.HTTP_201_CREATED

        # Verify auto-link was created
        profile = patient_user.patient_profile
        assert profile.therapist_links.filter(therapist=therapist1, status=LinkStatus.ACTIVE).exists()
