"""Testy jednostkowe i integracyjne dla endpointu /auth/me/ oraz UpdateMeSerializer.

Weryfikuje pobieranie danych aktualnego profilu oraz walidację i aktualizację
imienia i nazwiska zgodnie ze standardem 5 Filarów Walidacji PhysioCare.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from accounts.mfa import generate_totp_secret
from accounts.models import UserMFA
from core.field_policies import LAST_NAME_REQUIRED, NAME_REQUIRED

User = get_user_model()


@pytest.mark.django_db
class TestCurrentUserEndpoint:
    """Testy pobierania i aktualizacji danych bieżącego użytkownika."""

    def test_get_current_user_unauthenticated_returns_401(self, api_client: APIClient) -> None:
        # Act
        response = api_client.get('/api/v1/auth/me/')

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_authenticated_returns_200(
        self, api_client: APIClient, admin_user: User
    ) -> None:
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        response = api_client.get('/api/v1/auth/me/')

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['user']['id'] == str(admin_user.id)
        assert data['user']['email'] == admin_user.email
        assert data['user']['role'] == 'ADMIN'
        assert data['user']['has_mfa'] is False
        assert data['user']['mfa_required'] is True

    def test_get_current_user_mfa_flags_when_mfa_enabled(
        self, api_client: APIClient, admin_user: User
    ) -> None:
        # Arrange
        UserMFA.objects.create(
            user=admin_user,
            secret_key=generate_totp_secret(),
            is_enabled=True,
        )
        api_client.force_authenticate(user=admin_user)

        # Act
        response = api_client.get('/api/v1/auth/me/')

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['user']['has_mfa'] is True
        assert data['user']['mfa_required'] is True

    def test_get_current_user_mfa_flags_for_patient(
        self, api_client: APIClient, patient: object
    ) -> None:
        # Arrange
        api_client.force_authenticate(user=patient.user)

        # Act
        response = api_client.get('/api/v1/auth/me/')

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['user']['role'] == 'PATIENT'
        assert data['user']['has_mfa'] is False
        assert data['user']['mfa_required'] is False

    def test_patch_current_user_updates_first_and_last_name(
        self, api_client: APIClient, admin_user: User
    ) -> None:
        # Arrange
        api_client.force_authenticate(user=admin_user)
        payload = {'first_name': 'Jan', 'last_name': 'Kowalski'}

        # Act
        response = api_client.patch('/api/v1/auth/me/', payload, format='json')

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['user']['first_name'] == 'Jan'
        assert data['user']['last_name'] == 'Kowalski'

        admin_user.refresh_from_db()
        assert admin_user.first_name == 'Jan'
        assert admin_user.last_name == 'Kowalski'

    @pytest.mark.parametrize(
        ('payload', 'expected_field', 'expected_msg'),
        [
            ({'first_name': ''}, 'first_name', NAME_REQUIRED),
            ({'first_name': '   '}, 'first_name', NAME_REQUIRED),
            ({'last_name': ''}, 'last_name', LAST_NAME_REQUIRED),
            ({'last_name': '   '}, 'last_name', LAST_NAME_REQUIRED),
            ({'first_name': 'A' * 101}, 'first_name', '100'),
            ({'last_name': 'B' * 101}, 'last_name', '100'),
        ],
    )
    def test_patch_current_user_validation_failures(
        self,
        api_client: APIClient,
        admin_user: User,
        payload: dict[str, str],
        expected_field: str,
        expected_msg: str,
    ) -> None:
        # Arrange
        api_client.force_authenticate(user=admin_user)

        # Act
        response = api_client.patch('/api/v1/auth/me/', payload, format='json')

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_data = response.json()
        assert expected_field in str(error_data)
        assert expected_msg in str(error_data)
