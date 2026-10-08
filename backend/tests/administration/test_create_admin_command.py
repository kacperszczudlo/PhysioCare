"""Testy integracyjne dla komendy Django manage.py create_admin."""

import io

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from accounts.models import RoleChoices
from patients.models import PatientProfile

User = get_user_model()


@pytest.mark.django_db
class TestCreateAdminManagementCommand:
    """Weryfikuje działanie komendy create_admin w różnych scenariuszach."""

    def test_create_new_admin_success(self) -> None:
        """Weryfikuje pomyślne utworzenie nowego konta administratora z prawami is_staff i is_superuser."""
        email = 'new.admin@physiocare.test'
        password = 'StrongPassword123!'
        out = io.StringIO()

        call_command(
            'create_admin',
            email=email,
            password=password,
            first_name='Jan',
            last_name='Kowalski',
            noinput=True,
            stdout=out,
        )

        user = User.objects.get(email=email)
        assert user.role == RoleChoices.ADMIN
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.is_active is True
        assert user.email_verified_at is not None
        assert user.check_password(password) is True
        assert 'SUKCES' in out.getvalue()

    def test_promote_existing_user(self, patient: PatientProfile) -> None:
        """Weryfikuje awans istniejącego pacjenta na rolę administratora bez naruszania pozostałych danych."""
        user = patient.user
        assert user.role == RoleChoices.PATIENT
        assert user.is_staff is False
        assert user.is_superuser is False
        out = io.StringIO()

        call_command(
            'create_admin',
            email=user.email,
            promote=True,
            noinput=True,
            stdout=out,
        )

        user.refresh_from_db()
        assert user.role == RoleChoices.ADMIN
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.is_active is True
        assert 'awansowany' in out.getvalue()

    def test_reject_weak_password_enforces_policy(self) -> None:
        """Weryfikuje odrzucenie zbyt słabego hasła niezgodnego z polityką bezpieczeństwa."""
        email = 'weak.admin@physiocare.test'
        weak_password = '123'  # za krótkie, brak znaków specjalnych

        with pytest.raises(CommandError, match='wymogów bezpieczeństwa'):
            call_command(
                'create_admin',
                email=email,
                password=weak_password,
                noinput=True,
            )

        assert not User.objects.filter(email=email).exists()

    def test_password_from_environment_variable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Weryfikuje odczyt hasła administratora ze zmiennej środowiskowej DJANGO_SUPERUSER_PASSWORD."""
        email = 'env.admin@physiocare.test'
        env_password = 'EnvPassword123!@#'
        monkeypatch.setenv('DJANGO_SUPERUSER_PASSWORD', env_password)
        out = io.StringIO()

        call_command(
            'create_admin',
            email=email,
            noinput=True,
            stdout=out,
        )

        user = User.objects.get(email=email)
        assert user.check_password(env_password) is True
        assert user.role == RoleChoices.ADMIN
        assert 'SUKCES' in out.getvalue()

    def test_generate_sql_does_not_modify_database(self) -> None:
        """Weryfikuje generowanie czystego zapytania SQL bez modyfikacji lokalnej bazy danych."""
        email = 'sql.admin@physiocare.test'
        password = 'SqlPassword123!'
        out = io.StringIO()

        call_command(
            'create_admin',
            email=email,
            password=password,
            generate_sql=True,
            stdout=out,
        )

        output = out.getvalue()
        assert 'INSERT INTO users' in output
        assert email in output
        # Użytkownik nie powinien zostać utworzony w bazie
        assert not User.objects.filter(email=email).exists()

    def test_promote_nonexistent_user_raises_error(self) -> None:
        """Weryfikuje rzucenie błędu CommandError przy próbie awansu nieistniejącego użytkownika."""
        with pytest.raises(CommandError, match='nie istnieje'):
            call_command(
                'create_admin',
                email='nonexistent@physiocare.test',
                promote=True,
                noinput=True,
            )

