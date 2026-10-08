"""Testy jednostkowe klas uprawnień administracyjnych oraz polityki wymogu 2FA.

Weryfikuje klasę IsAdminRole (w tym wyjątek TypeError dla request=None,
odrzucanie ról PATIENT/THERAPIST oraz akceptację roli ADMIN/staff/superuser)
oraz regułę is_mfa_required_for_user.
"""

from unittest.mock import Mock

import pytest

from accounts.models import RoleChoices
from accounts.views import is_mfa_required_for_user
from core.permissions import IsAdminRole


class TestIsAdminRolePermission:
    """Testy jednostkowe uprawnienia IsAdminRole."""

    def test_has_permission_raises_type_error_when_request_is_none(self) -> None:
        # Arrange
        perm = IsAdminRole()

        # Act & Assert
        with pytest.raises(TypeError, match="Argument 'request' nie może być None."):
            perm.has_permission(request=None, view=Mock())

    def test_has_permission_returns_false_for_unauthenticated_request(self) -> None:
        # Arrange
        perm = IsAdminRole()
        request = Mock()
        request.user = Mock(is_authenticated=False)

        # Act
        result = perm.has_permission(request=request, view=Mock())

        # Assert
        assert result is False

    @pytest.mark.parametrize('role', [RoleChoices.PATIENT, RoleChoices.THERAPIST, 'UNKNOWN', None])
    def test_has_permission_returns_false_for_non_admin_roles(self, role: str | None) -> None:
        # Arrange
        perm = IsAdminRole()
        request = Mock()
        request.user = Mock(is_authenticated=True, role=role, is_staff=False, is_superuser=False)

        # Act
        result = perm.has_permission(request=request, view=Mock())

        # Assert
        assert result is False

    def test_has_permission_returns_true_for_admin_role(self) -> None:
        # Arrange
        perm = IsAdminRole()
        request = Mock()
        request.user = Mock(is_authenticated=True, role=RoleChoices.ADMIN, is_staff=False, is_superuser=False)

        # Act
        result = perm.has_permission(request=request, view=Mock())

        # Assert
        assert result is True

    @pytest.mark.parametrize(('is_staff', 'is_superuser'), [(True, False), (False, True), (True, True)])
    def test_has_permission_returns_true_for_staff_or_superuser(
        self, is_staff: bool, is_superuser: bool
    ) -> None:
        # Arrange
        perm = IsAdminRole()
        request = Mock()
        request.user = Mock(
            is_authenticated=True,
            role=RoleChoices.PATIENT,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )

        # Act
        result = perm.has_permission(request=request, view=Mock())

        # Assert
        assert result is True


class TestIsMfaRequiredForUser:
    """Testy polityki obowiązkowego 2FA dla poszczególnych ról."""

    def test_mfa_not_required_when_user_is_none(self) -> None:
        # Act & Assert
        assert is_mfa_required_for_user(None) is False

    def test_mfa_not_required_for_regular_patient(self) -> None:
        # Arrange
        user = Mock(role=RoleChoices.PATIENT, is_staff=False, is_superuser=False)

        # Act & Assert
        assert is_mfa_required_for_user(user) is False

    @pytest.mark.parametrize('role', [RoleChoices.THERAPIST, RoleChoices.ADMIN])
    def test_mfa_required_for_therapist_and_admin(self, role: str) -> None:
        # Arrange
        user = Mock(role=role, is_staff=False, is_superuser=False)

        # Act & Assert
        assert is_mfa_required_for_user(user) is True

    @pytest.mark.parametrize(('is_staff', 'is_superuser'), [(True, False), (False, True)])
    def test_mfa_required_for_staff_and_superuser_regardless_of_role(
        self, is_staff: bool, is_superuser: bool
    ) -> None:
        # Arrange
        user = Mock(role=RoleChoices.PATIENT, is_staff=is_staff, is_superuser=is_superuser)

        # Act & Assert
        assert is_mfa_required_for_user(user) is True
