from typing import TYPE_CHECKING

from scheduling.therapy_type_presets import (
    THERAPY_TYPE_PRESETS,
    ensure_therapy_type_presets,
    preset_payloads,
)

if TYPE_CHECKING:
    from therapists.models import TherapistProfile


def test_preset_payloads_cover_kinds_and_profiles() -> None:
    """Sprawdza, czy przygotowane payloady szablonów typów terapii pokrywają grupy kind oraz profile."""
    # Arrange
    payloads = preset_payloads()
    # Assert
    assert len(payloads) == len(THERAPY_TYPE_PRESETS)
    groups = {item['group'] for item in payloads}
    assert groups == {'kind', 'profile'}
    assert any(item['name'] == 'Wizyta konsultacyjna' for item in payloads)
    assert any(item['name'] == 'Neurologiczna' for item in payloads)


def test_ensure_therapy_type_presets_is_idempotent(therapist: 'TherapistProfile') -> None:
    """Sprawdza idempotentność generowania domyślnych typów terapii dla fizjoterapeuty."""
    # Arrange
    first = ensure_therapy_type_presets(therapist)
    # Assert
    assert len(first) == len(THERAPY_TYPE_PRESETS)

    second = ensure_therapy_type_presets(therapist)
    assert len(second) == len(THERAPY_TYPE_PRESETS)
    assert {item.name for item in first} == {item.name for item in second}

