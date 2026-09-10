
from therapists.competence import QualificationLevel
from therapists.medical_devices import (
    DEVICE_CATALOG,
    catalog_as_list,
    get_device,
    groups_summary,
)


def test_catalog_as_list_without_qualification_returns_all_allowed():
    # Act
    items = catalog_as_list()

    # Assert
    assert len(items) == len(DEVICE_CATALOG)
    assert all(item['allowed_for_therapist'] is True for item in items)


def test_catalog_as_list_for_licencjat_restricts_magister_and_spec_devices():
    # Act
    items = catalog_as_list(qualification_level=QualificationLevel.LICENCJAT)

    # Assert
    # Licencjat cannot order MAGISTER or FIZJO_SPEC devices
    assert all(item['allowed_for_therapist'] is False for item in items)


def test_catalog_as_list_for_magister_allows_magister_blocks_spec():
    # Act
    items = catalog_as_list(qualification_level=QualificationLevel.MAGISTER)

    # Assert
    magister_items = [i for i in items if i['min_qualification'] == QualificationLevel.MAGISTER]
    spec_items = [i for i in items if i['min_qualification'] == QualificationLevel.FIZJO_SPEC]

    assert len(magister_items) > 0
    assert len(spec_items) > 0
    assert all(i['allowed_for_therapist'] is True for i in magister_items)
    assert all(i['allowed_for_therapist'] is False for i in spec_items)


def test_catalog_as_list_for_fizjo_spec_allows_all():
    # Act
    items = catalog_as_list(qualification_level=QualificationLevel.FIZJO_SPEC)

    # Assert
    assert all(i['allowed_for_therapist'] is True for i in items)


def test_get_device_by_valid_code():
    # Act
    device = get_device('J.ANKLE')

    # Assert
    assert device is not None
    assert device['code'] == 'J.ANKLE'
    assert device['group'] == 'J'
    assert device['name'] == 'Orteza stabilizująca staw skokowy (seryjna)'


def test_get_device_by_invalid_code_returns_none():
    # Act & Assert
    assert get_device('INVALID.CODE.999') is None


def test_groups_summary():
    # Act
    summary = groups_summary()

    # Assert
    assert 'magister_groups' in summary
    assert 'fizjo_spec_extra_groups' in summary
    assert isinstance(summary['magister_groups'], list)
    assert isinstance(summary['fizjo_spec_extra_groups'], list)
    assert len(summary['magister_groups']) > 0
