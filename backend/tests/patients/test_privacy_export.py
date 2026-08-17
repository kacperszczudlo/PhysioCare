from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from scheduling.models import Visit, VisitStatus


@pytest.mark.django_db
def test_data_export_includes_clinical_collections(
    api_client, patient, therapist, therapy_type,
):
    Visit.objects.create(
        patient=patient,
        therapist=therapist,
        therapy_type=therapy_type,
        start_at=timezone.now(),
        end_at=timezone.now() + timedelta(minutes=45),
        status=VisitStatus.SCHEDULED,
    )
    token = str(RefreshToken.for_user(patient.user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    response = api_client.post('/api/v1/me/data-export/', {}, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert 'profile' in response.data
    assert 'consents' in response.data
    assert 'visits' in response.data
    assert 'episodes' in response.data
    assert 'documents' in response.data
    assert 'exercise_assignments' in response.data
    assert len(response.data['visits']) == 1
