"""Testy jednostkowe narzędzia skryptowego do generowania zapytań SQL dla administratora.

Weryfikuje czystą funkcję generowania zapytań SQL bez efektów ubocznych w bazie.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / 'scripts'
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from create_admin import generate_sql_queries  # noqa: E402


class TestCreateAdminScriptSqlGenerator:
    """Testy generatora zapytań SQL INSERT/UPDATE."""

    def test_generate_sql_queries_contains_required_statements(self) -> None:
        # Arrange
        email = 'admin.test@physiocare.test'
        password = 'SecretPassword123!'
        first_name = 'Anna'
        last_name = 'Admin'

        # Act
        sql = generate_sql_queries(
            email=email, password=password, first_name=first_name, last_name=last_name
        )

        # Assert
        assert 'INSERT INTO users' in sql
        assert 'UPDATE users' in sql
        assert "role = 'ADMIN'" in sql
        assert email in sql
        assert first_name in sql
        assert last_name in sql
        assert ('pbkdf2_sha256$' in sql or 'md5$' in sql)  # weryfikacja wygenerowania poprawnego hasha Django

    def test_generate_sql_escapes_single_quotes(self) -> None:
        # Arrange
        email = 'o\'connor@physiocare.test'
        password = 'Password123!'
        first_name = 'O\'Brian'
        last_name = 'D\'Arcy'

        # Act
        sql = generate_sql_queries(
            email=email, password=password, first_name=first_name, last_name=last_name
        )

        # Assert
        assert "o''connor@physiocare.test" in sql
        assert "O''Brian" in sql
        assert "D''Arcy" in sql
