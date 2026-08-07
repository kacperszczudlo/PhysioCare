from scheduling.therapy_type_presets import (
    THERAPY_TYPE_PRESETS,
    ensure_therapy_type_presets,
    preset_payloads,
)


def test_preset_payloads_cover_kinds_and_profiles():
    payloads = preset_payloads()
    assert len(payloads) == len(THERAPY_TYPE_PRESETS)
    groups = {item['group'] for item in payloads}
    assert groups == {'kind', 'profile'}
    assert any(item['name'] == 'Wizyta konsultacyjna' for item in payloads)
    assert any(item['name'] == 'Neurologiczna' for item in payloads)


def test_ensure_therapy_type_presets_is_idempotent(therapist):
    first = ensure_therapy_type_presets(therapist)
    assert len(first) == len(THERAPY_TYPE_PRESETS)

    second = ensure_therapy_type_presets(therapist)
    assert len(second) == len(THERAPY_TYPE_PRESETS)
    assert {item.name for item in first} == {item.name for item in second}
