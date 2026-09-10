import pytest
from rest_framework.exceptions import ValidationError

from treatment.serializers import (
    BodyAreaPainSerializer,
    MedicalDeviceOrderSerializer,
    TreatmentEpisodeCreateSerializer,
)


def test_treatment_episode_serializer_valid_icd10():
    # Arrange
    serializer = TreatmentEpisodeCreateSerializer(data={
        'icd10_code': 'M54.5',
        'summary_note': 'Ból odcinka lędźwiowego',
    })

    # Act & Assert
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data['icd10_code'] == 'M54.5'


def test_treatment_episode_serializer_invalid_icd10():
    # Arrange
    serializer = TreatmentEpisodeCreateSerializer(data={
        'icd10_code': 'INVALID-ICD10-CODE',
    })

    # Act
    is_valid = serializer.is_valid()

    # Assert
    assert is_valid is False
    assert 'icd10_code' in serializer.errors


def test_treatment_episode_serializer_functional_diagnosis_too_long():
    # Arrange
    serializer = TreatmentEpisodeCreateSerializer(data={
        'functional_diagnosis': 'A' * 5001,
    })

    # Act & Assert
    assert serializer.is_valid() is False
    assert 'functional_diagnosis' in serializer.errors


@pytest.mark.parametrize('valid_vas', [0, 5, 10])
def test_body_area_pain_serializer_valid_vas(valid_vas):
    # Arrange
    serializer = BodyAreaPainSerializer(data={
        'body_region': 'Kręgosłup lędźwiowy',
        'view_side': 'BACK',
        'vas_score': valid_vas,
        'pain_character': ['Pieczenie', 'Kłucie'],
        'treatment_targets': ['Redukcja bólu'],
    })

    # Act & Assert
    assert serializer.is_valid(), serializer.errors


@pytest.mark.parametrize('invalid_vas', [-1, 11])
def test_body_area_pain_serializer_invalid_vas(invalid_vas):
    # Arrange
    serializer = BodyAreaPainSerializer(data={
        'body_region': 'Brak',
        'view_side': 'BACK',
        'vas_score': invalid_vas,
    })

    # Act & Assert
    assert serializer.is_valid() is False
    assert 'vas_score' in serializer.errors


def test_body_area_pain_serializer_invalid_character_type():
    # Arrange
    serializer = BodyAreaPainSerializer(data={
        'body_region': 'Kolano',
        'vas_score': 5,
        'pain_character': 'not-a-list',
    })

    # Act & Assert
    assert serializer.is_valid() is False
    assert 'pain_character' in serializer.errors


@pytest.mark.parametrize(
    'code,is_valid_code',
    [
        ('1234', True),
        ('', True),
        ('12', False),
        ('ABCD', False),
    ],
)
def test_medical_device_order_access_code_validation(code, is_valid_code):
    # Arrange
    serializer = MedicalDeviceOrderSerializer()

    # Act
    if is_valid_code:
        assert serializer.validate_access_code(code) == code.strip()
    else:
        with pytest.raises(ValidationError):
            serializer.validate_access_code(code)
