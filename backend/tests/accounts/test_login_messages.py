import pytest
from django.urls import reverse
from rest_framework import status

LOGIN_FAIL_MESSAGE = 'Nieprawidłowy e-mail lub hasło.'


@pytest.mark.django_db
def test_login_unknown_email_returns_generic_message(api_client):
    url = reverse('login')
    response = api_client.post(
        url,
        {'email': 'brak@example.com', 'password': 'Anything1!'},
        format='json',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['error']['code'] == 'AUTH_001'
    assert response.data['error']['message'] == LOGIN_FAIL_MESSAGE


@pytest.mark.django_db
def test_login_wrong_password_returns_same_generic_message(api_client, patient):
    url = reverse('login')
    response = api_client.post(
        url,
        {'email': patient.user.email, 'password': 'WrongPass1!'},
        format='json',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['error']['code'] == 'AUTH_001'
    assert response.data['error']['message'] == LOGIN_FAIL_MESSAGE
