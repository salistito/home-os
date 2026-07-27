import pytest


@pytest.fixture(autouse=True)
def _apply_food_migration(monkeypatch):
    monkeypatch.setattr(
        "core.db._current_schema_version",
        lambda: "20260718_000000_users_integer_pk_soft_delete_roles.py",
    )
