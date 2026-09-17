import pytest

from notifications.keys import CANONICAL_PREF_KEYS, NotificationPreferenceKey, get_canonical_pref_keys, is_valid_pref_key


def test_get_canonical_pref_keys() -> None:
    """Sprawdza poprawność pobierania krotki kanonicznych kluczy preferencji."""
    # Arrange
    keys: tuple[str, ...] = get_canonical_pref_keys()
    # Assert
    assert isinstance(keys, tuple)
    assert len(keys) == len(NotificationPreferenceKey.choices)
    assert 'visit_reminder' in keys
    assert 'new_document' in keys


def test_is_valid_pref_key() -> None:
    """Sprawdza działanie walidacji kluczy oraz sprawdzanie typów."""
    # Arrange
    # Assert
    assert is_valid_pref_key('visit_reminder') is True
    assert is_valid_pref_key('invalid_key') is False
    # Act

    with pytest.raises(TypeError, match="Argument 'key' musi być typu str."):
        is_valid_pref_key(12345)  # type: ignore[arg-type]

