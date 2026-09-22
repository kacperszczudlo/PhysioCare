from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from treatment.models import FundingHint, RecommendationType
from treatment.serializers import (
    DiagnosticRecommendationSerializer,
    PhysicianOrderRefusalSerializer,
    ReceptaNaRuchReferralSerializer,
)

if TYPE_CHECKING:
    from therapists.models import TherapistProfile


@pytest.mark.django_db
def test_diagnostic_recommendation_mri_private_funding_preserved(therapist: 'TherapistProfile') -> None:
    """Sprawdza zachowanie prywatnego finansowania dla rekomendacji badania rezonansu (MRI)."""
    # Arrange
    request_mock: MagicMock = MagicMock()
    request_mock.user = therapist.user

    ser = DiagnosticRecommendationSerializer(
        data={
            'recommendation_type': RecommendationType.IMAGING_MRI,
            'justification': 'Podejrzenie uszkodzenia łąkotki bocznej',
            'funding_hint': FundingHint.PRIVATE,
        },
        context={'request': request_mock},
    )

    # Assert
    assert ser.is_valid(), ser.errors
    assert ser.validated_data['funding_hint'] == FundingHint.PRIVATE


@pytest.mark.django_db
def test_diagnostic_recommendation_rtg_forces_nfz_via_doctor(therapist: 'TherapistProfile') -> None:
    """Sprawdza automatyczne przypisanie trybu NFZ przez lekarza dla rekomendacji badania RTG."""
    # Arrange
    request_mock: MagicMock = MagicMock()
    request_mock.user = therapist.user

    ser = DiagnosticRecommendationSerializer(
        data={
            'recommendation_type': RecommendationType.IMAGING_RTG,
            'justification': 'Ocena stanu odcinka L-S',
            'funding_hint': FundingHint.PRIVATE,
        },
        context={'request': request_mock},
    )

    # Assert
    assert ser.is_valid(), ser.errors
    assert ser.validated_data['funding_hint'] == FundingHint.NFZ_VIA_DOCTOR


def test_physician_order_refusal_requires_description_and_reason() -> None:
    """Sprawdza wymóg podania opisu zlecenia lekarskiego oraz uzasadnienia przy odmowie jego wykonania."""
    # Arrange
    ser = PhysicianOrderRefusalSerializer(data={
        'physician_order_description': '   ',
        'refusal_reason': 'Przeciwwskazanie bezwzględne',
    })
    # Assert
    assert ser.is_valid() is False
    assert 'physician_order_description' in ser.errors

    ser = PhysicianOrderRefusalSerializer(data={
        'physician_order_description': 'Zlecenie krioterapii',
        'refusal_reason': '   ',
    })
    assert ser.is_valid() is False
    assert 'refusal_reason' in ser.errors



def test_recepta_na_ruch_requires_readiness_confirmed() -> None:
    """Sprawdza odrzucenie skierowania na Receptę na Ruch bez potwierdzonej gotowości pacjenta."""
    # Arrange
    ser = ReceptaNaRuchReferralSerializer(data={
        'readiness_confirmed': False,
        'activity_notes': 'Spacer 30 min dziennie',
    })

    # Assert
    assert ser.is_valid() is False
    assert 'readiness_confirmed' in ser.errors

