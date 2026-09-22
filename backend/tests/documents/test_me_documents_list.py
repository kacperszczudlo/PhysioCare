import pytest
from rest_framework import status

from documents.models import MedicalDocument


@pytest.mark.django_db
def test_patient_lists_own_medical_documents(
    api_client: object, patient: object, therapist: object,
) -> None:
    """Sprawdza pobieranie listy własnych dokumentów medycznych przez zalogowanego pacjenta."""
    # Arrange
    MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Wynik RTG Kręgosłupa',
        file_url='/media/documents/rtg.pdf',
        mime_type='application/pdf',
    )
    MedicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist.user,
        title='Karta USG',
        file_url='/media/documents/usg.pdf',
        mime_type='application/pdf',
    )

    api_client.force_authenticate(user=patient.user)

    response: object = api_client.get('/api/v1/me/documents/')

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 2
    titles: set[str] = {item['title'] for item in response.data['results']}
    assert titles == {'Karta USG', 'Wynik RTG Kręgosłupa'}


@pytest.mark.django_db
def test_patient_without_documents_returns_empty_list(
    api_client: object, patient: object,
) -> None:
    """Sprawdza zwrócenie pustej listy dokumentów gdy pacjent nie posiada jeszcze dokumentacji."""
    # Arrange
    api_client.force_authenticate(user=patient.user)

    response: object = api_client.get('/api/v1/me/documents/')

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 0
    assert response.data['results'] == []


@pytest.mark.django_db
def test_therapist_cannot_access_patient_me_documents(
    api_client: object, therapist: object,
) -> None:
    """Sprawdza odmowę dostępu fizjoterapeuty do punktu końcowego listy dokumentów pacjenta /me/documents/."""
    # Arrange
    api_client.force_authenticate(user=therapist.user)

    response: object = api_client.get('/api/v1/me/documents/')

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_unauthenticated_user_cannot_list_me_documents(api_client: object) -> None:
    """Sprawdza odrzucenie zapytania niezalogowanego użytkownika o listę dokumentów /me/documents/."""
    # Arrange
    response: object = api_client.get('/api/v1/me/documents/')

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

