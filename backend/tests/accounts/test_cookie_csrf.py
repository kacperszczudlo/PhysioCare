"""Testy ochrony CSRF przy uwierzytelnieniu za pomocą ciasteczek HTTP (CookieJWTAuthentication)."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.mark.django_db
class TestCookieJwtCsrfProtection:
    """Weryfikacja blokowania nieautoryzowanych żądań międzywitrynowych (CSRF)."""

    def test_untrusted_origin_with_cookie_auth_is_blocked(self) -> None:
        """Weryfikuje, że żądanie modyfikujące stan z obcego Origin przy sesji ciasteczkowej jest blokowane z kodem 403."""
        user = User.objects.create_user(
            email='patient.csrf@physiocare.test',
            password='StrongPassword123!',
            first_name='Jan',
            last_name='Kowalski',
            role='PATIENT',
        )
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.cookies['access_token'] = access_token

        # Żądanie POST z ciasteczkiem i obcym Originem (atak CSRF)
        response = client.post(
            '/api/v1/auth/logout/',
            {},
            format='json',
            HTTP_ORIGIN='https://evil-attacker-site.com',
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'CSRF' in str(response.data)

    def test_trusted_origin_with_cookie_auth_is_allowed(self) -> None:
        """Weryfikuje, że żądanie z zaufanego Origin (np. Cloudflare Pages projektu) jest pomyślnie autoryzowane."""
        user = User.objects.create_user(
            email='patient.trusted@physiocare.test',
            password='StrongPassword123!',
            first_name='Jan',
            last_name='Kowalski',
            role='PATIENT',
        )
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.cookies['access_token'] = access_token

        # Żądanie POST z ciasteczkiem i zaufanym Originem
        response = client.post(
            '/api/v1/auth/logout/',
            {},
            format='json',
            HTTP_ORIGIN='https://physiocare-3yh.pages.dev',
        )

        assert response.status_code == status.HTTP_200_OK

    def test_bearer_token_ignores_untrusted_origin_for_mobile_apps(self) -> None:
        """Weryfikuje, że zapytania z nagłówkiem Authorization Bearer nie podlegają restrykcjom Origin CSRF."""
        user = User.objects.create_user(
            email='mobile.user@physiocare.test',
            password='StrongPassword123!',
            first_name='Jan',
            last_name='Kowalski',
            role='PATIENT',
        )
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Bearer token (aplikacja mobilna) nie korzysta z ciasteczek, więc nie podlega atakom CSRF
        response = client.post(
            '/api/v1/auth/logout/',
            {},
            format='json',
            HTTP_ORIGIN='https://some-custom-origin.com',
        )

        assert response.status_code == status.HTTP_200_OK

