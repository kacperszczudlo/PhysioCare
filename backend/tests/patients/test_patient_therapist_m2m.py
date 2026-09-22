import pytest
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import CustomUser, RoleChoices
from patients.models import LinkStatus, PatientProfile
from scheduling.models import TherapyType
from therapists.models import TherapistProfile


@pytest.fixture
def therapist1(db: object) -> TherapistProfile:
    """Tworzy pierwszego fizjoterapeutę testowego."""
    user: CustomUser = CustomUser.objects.create_user(
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
def therapist2(db: object) -> TherapistProfile:
    """Tworzy drugiego fizjoterapeutę testowego."""
    user: CustomUser = CustomUser.objects.create_user(
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
def patient_user(db: object) -> CustomUser:
    """Tworzy użytkownika-pacjenta testowego."""
    user: CustomUser = CustomUser.objects.create_user(
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
    """Zbiór testów dla relacji wielu-do-wielu (M2M) pomiędzy pacjentami i fizjoterapeutami."""

    def test_register_patient_without_therapist(self) -> None:
        """Sprawdza rejestrację pacjenta bez przypisanego kodem fizjoterapeuty."""
        # Arrange
        client: APIClient = APIClient()
        response: object = client.post(
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
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        profile: PatientProfile = PatientProfile.objects.get(user__email='newpatient@example.com')
        assert profile.therapist_links.count() == 0

    def test_register_patient_with_therapist_code(self, therapist1: TherapistProfile) -> None:
        """Sprawdza automatyczne powiązanie pacjenta z fizjoterapeutą podczas rejestracji kodem PWZF."""
        # Arrange
        client: APIClient = APIClient()
        response: object = client.post(
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
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        profile: PatientProfile = PatientProfile.objects.get(user__email='codedpatient@example.com')
        assert profile.therapist_links.filter(therapist=therapist1, status=LinkStatus.ACTIVE).exists()

    def test_link_and_unlink_therapist_endpoints(
        self, patient_user: CustomUser, therapist1: TherapistProfile, therapist2: TherapistProfile,
    ) -> None:
        """Sprawdza punkty końcowe dodawania i usuwania powiązania fizjoterapeuty przez pacjenta."""
        # Arrange
        client: APIClient = APIClient()
        client.force_authenticate(user=patient_user)

        res: object = client.get('/api/v1/me/therapists/')
        # Assert
        assert res.status_code == status.HTTP_200_OK
        data: object = res.data.get('results', res.data) if isinstance(res.data, dict) else res.data
        assert len(data) == 0

        link_res: object = client.post(
            '/api/v1/me/therapists/link/',
            {'therapist_id': str(therapist1.id)},
            format='json',
        )
        assert link_res.status_code == status.HTTP_201_CREATED

        link_res2: object = client.post(
            '/api/v1/me/therapists/link/',
            {'therapist_code': therapist2.pwzf_number},
            format='json',
        )
        assert link_res2.status_code == status.HTTP_201_CREATED
        # Act

        res = client.get('/api/v1/me/therapists/')
        data = res.data.get('results', res.data) if isinstance(res.data, dict) else res.data
        assert len(data) == 2

        unlink_res: object = client.delete(f'/api/v1/me/therapists/{therapist1.id}/')
        assert unlink_res.status_code == status.HTTP_200_OK

        res_after: object = client.get('/api/v1/me/therapists/')
        data_after: object = res_after.data.get('results', res_after.data) if isinstance(res_after.data, dict) else res_after.data
        assert len(data_after) == 1
        assert data_after[0]['id'] == str(therapist2.id)

    def test_public_therapist_search(
        self, patient_user: CustomUser, therapist1: TherapistProfile, therapist2: TherapistProfile,
    ) -> None:
        """Sprawdza publiczne wyszukiwanie fizjoterapeutów po nazwisku przez pacjenta."""
        # Arrange
        client: APIClient = APIClient()
        client.force_authenticate(user=patient_user)

        res: object = client.get('/api/v1/therapists/public/?search=Kowalski')
        # Assert
        assert res.status_code == status.HTTP_200_OK
        results: object = res.data.get('results', res.data) if isinstance(res.data, dict) else res.data
        assert len(results) == 1
        assert results[0]['id'] == str(therapist1.id)

    def test_auto_link_on_visit_booking(
        self, patient_user: CustomUser, therapist1: TherapistProfile,
    ) -> None:
        """Sprawdza automatyczne utworzenie relacji z fizjoterapeutą po zarezerwowaniu u niego wizyty."""
        # Arrange
        client: APIClient = APIClient()
        client.force_authenticate(user=patient_user)

        tt: TherapyType = TherapyType.objects.create(
            therapist=therapist1,
            name='Konsultacja fizjoterapeutyczna',
            duration_min=45,
        )

        import datetime

        from django.utils import timezone

        start: object = timezone.now() + datetime.timedelta(days=2)
        end: object = start + datetime.timedelta(minutes=45)

        from scheduling.models import TherapistAvailabilitySlot
        TherapistAvailabilitySlot.objects.create(
            therapist=therapist1,
            is_recurring=False,
            start_at=start - datetime.timedelta(hours=1),
            end_at=end + datetime.timedelta(hours=1),
            is_active=True,
        )

        visit_res: object = client.post(
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
        # Assert
        assert visit_res.status_code == status.HTTP_201_CREATED

        profile: PatientProfile = patient_user.patient_profile
        assert profile.therapist_links.filter(therapist=therapist1, status=LinkStatus.ACTIVE).exists()

