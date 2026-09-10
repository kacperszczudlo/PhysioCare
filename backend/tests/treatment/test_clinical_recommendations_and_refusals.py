from unittest.mock import MagicMock

import pytest

from treatment.models import FundingHint, RecommendationType
from treatment.serializers import (
    DiagnosticRecommendationSerializer,
    PhysicianOrderRefusalSerializer,
    ReceptaNaRuchReferralSerializer,
)


@pytest.mark.django_db
def test_diagnostic_recommendation_mri_private_funding_preserved(therapist):
    # Arrange
    request_mock = MagicMock()
    request_mock.user = therapist.user

    ser = DiagnosticRecommendationSerializer(
        data={
            'recommendation_type': RecommendationType.IMAGING_MRI,
            'justification': 'Podejrzenie uszkodzenia łąkotki bocznej',
            'funding_hint': FundingHint.PRIVATE,
        },
        context={'request': request_mock},
    )

    # Act & Assert
    assert ser.is_valid(), ser.errors
    assert ser.validated_data['funding_hint'] == FundingHint.PRIVATE


@pytest.mark.django_db
def test_diagnostic_recommendation_rtg_forces_nfz_via_doctor(therapist):
    # Arrange
    request_mock = MagicMock()
    request_mock.user = therapist.user

    ser = DiagnosticRecommendationSerializer(
        data={
            'recommendation_type': RecommendationType.IMAGING_RTG,
            'justification': 'Ocena stanu odcinka L-S',
            'funding_hint': FundingHint.PRIVATE,
        },
        context={'request': request_mock},
    )

    # Act & Assert
    assert ser.is_valid(), ser.errors
    # RTG imaging requires doctor referral on NFZ
    assert ser.validated_data['funding_hint'] == FundingHint.NFZ_VIA_DOCTOR


def test_physician_order_refusal_requires_description_and_reason():
    # Blank description
    ser = PhysicianOrderRefusalSerializer(data={
        'physician_order_description': '   ',
        'refusal_reason': 'Przeciwwskazanie bezwzględne',
    })
    assert ser.is_valid() is False
    assert 'physician_order_description' in ser.errors

    # Blank reason
    ser = PhysicianOrderRefusalSerializer(data={
        'physician_order_description': 'Zlecenie krioterapii',
        'refusal_reason': '   ',
    })
    assert ser.is_valid() is False
    assert 'refusal_reason' in ser.errors


def test_recepta_na_ruch_requires_readiness_confirmed():
    ser = ReceptaNaRuchReferralSerializer(data={
        'readiness_confirmed': False,
        'activity_notes': 'Spacer 30 min dziennie',
    })

    # Act & Assert
    assert ser.is_valid() is False
    assert 'readiness_confirmed' in ser.errors
