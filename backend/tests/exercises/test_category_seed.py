import pytest

from exercises.category_seed import CATEGORY_SEED, LEGACY_CATEGORY_MAP, get_category_seed, resolve_legacy_category


def test_get_category_seed() -> None:
    """Sprawdza poprawność pobierania krotek początkowych kategorii."""
    # Arrange
    seed: list[tuple[str, str, str]] = get_category_seed()
    # Assert
    assert isinstance(seed, list)
    assert len(seed) == len(CATEGORY_SEED)
    assert seed[0] == (CATEGORY_SEED[0][0], CATEGORY_SEED[0][1], CATEGORY_SEED[0][2])


def test_resolve_legacy_category_valid() -> None:
    """Sprawdza poprawne mapowanie historycznych nazw kategorii."""
    # Arrange
    result: tuple[str, str] | None = resolve_legacy_category("Rozciąganie")
    # Assert
    assert result == ("TYPE", "stretching")

    unknown: tuple[str, str] | None = resolve_legacy_category("Nieznana Kategoria")
    assert unknown is None


def test_resolve_legacy_category_type_error() -> None:
    """Sprawdza rzucanie TypeError w przypadku podania niepoprawnego typu argumentu."""
    # Act
    with pytest.raises(TypeError, match="Argument 'name' musi być typu str."):
        resolve_legacy_category(12345)  # type: ignore[arg-type]

