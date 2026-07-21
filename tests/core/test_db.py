import pytest
import sqlite3

import core.db as core_db


@pytest.mark.integration
class TestGetConnection:
    def test_returns_sqlite3_connection(self, db_path, monkeypatch):
        monkeypatch.setattr(core_db, "HOME_OS_DB_PATH", str(db_path))
        conn = core_db.get_connection()
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_sets_row_factory_to_row(self, db_path, monkeypatch):
        monkeypatch.setattr(core_db, "HOME_OS_DB_PATH", str(db_path))
        conn = core_db.get_connection()
        assert conn.row_factory is sqlite3.Row
        conn.close()

    def test_enables_foreign_keys(self, db_path, monkeypatch):
        monkeypatch.setattr(core_db, "HOME_OS_DB_PATH", str(db_path))
        conn = core_db.get_connection()
        cursor = conn.execute("PRAGMA foreign_keys")
        assert cursor.fetchone()[0] == 1
        conn.close()

    def test_creates_db_directory_if_missing(self, tmp_path, monkeypatch):
        target_dir = tmp_path / "nested" / "subdir"
        db_file = target_dir / "test.db"
        monkeypatch.setattr(core_db, "HOME_OS_DB_PATH", str(db_file))
        assert not target_dir.exists()
        conn = core_db.get_connection()
        assert target_dir.exists()
        conn.close()

    def test_connection_is_usable(self, db_path, monkeypatch):
        monkeypatch.setattr(core_db, "HOME_OS_DB_PATH", str(db_path))
        conn = core_db.get_connection()
        conn.execute("SELECT 1")
        conn.close()


@pytest.mark.integration
class TestInitDb:
    def test_creates_database_file(self, db_path, monkeypatch):
        monkeypatch.setattr(core_db, "HOME_OS_DB_PATH", str(db_path))
        assert not db_path.exists()
        core_db.init_db()
        assert db_path.exists()

    def test_creates_all_tables(self, db_path, monkeypatch):
        monkeypatch.setattr(core_db, "HOME_OS_DB_PATH", str(db_path))
        core_db.init_db()
        conn = core_db.get_connection()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [t["name"] for t in tables]
        expected_tables = [
            "assignments",
            "finances_entries",
            "finances_entry_details",
            "finances_entry_tags",
            "finances_periods",
            "finances_tags",
            "reminders",
            "tasks",
            "users",
        ]
        for name in expected_tables:
            assert name in table_names, f"Table {name} not found"
        conn.close()

    def test_creates_users_table_with_correct_columns(self, db_path, monkeypatch):
        monkeypatch.setattr(core_db, "HOME_OS_DB_PATH", str(db_path))
        core_db.init_db()
        conn = core_db.get_connection()
        columns = conn.execute("PRAGMA table_info(users)").fetchall()
        col_names = {c["name"] for c in columns}
        expected = {"id", "name", "role", "password_hash", "telegram_chat_id", "deleted_at"}
        assert col_names == expected
        conn.close()

    def test_creates_indexes(self, db_path, monkeypatch):
        monkeypatch.setattr(core_db, "HOME_OS_DB_PATH", str(db_path))
        core_db.init_db()
        conn = core_db.get_connection()
        indexes = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
        ).fetchall()
        index_names = [i["name"] for i in indexes if i["name"] is not None]
        assert len(index_names) > 0
        conn.close()

    def test_is_idempotent(self, db_path, monkeypatch):
        monkeypatch.setattr(core_db, "HOME_OS_DB_PATH", str(db_path))
        core_db.init_db()
        core_db.init_db()
        conn = core_db.get_connection()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        assert len(tables) > 0
        conn.close()


@pytest.mark.integration
class TestRunMigrations:
    def test_skips_when_no_pending_migrations(self, db_path, tmp_path, monkeypatch):
        monkeypatch.setattr(core_db, "HOME_OS_DB_PATH", str(db_path))
        version_file = tmp_path / "SCHEMA_VERSION.txt"
        migrations = sorted(
            p
            for p in core_db._MIGRATIONS_DIR.iterdir()
            if p.suffix == ".py" and not p.stem.startswith("_")
        )
        if migrations:
            version_file.write_text(migrations[-1].name + "\n")
        else:
            version_file.write_text("no_migrations\n")
        monkeypatch.setattr(core_db, "_SCHEMA_VERSION_FILE", version_file)
        core_db.init_db()
        content = version_file.read_text().strip()
        assert content == migrations[-1].name if migrations else "no_migrations"
        conn = core_db.get_connection()
        conn.close()

    def test_applies_all_migrations_when_version_file_missing(self, db_path, tmp_path, monkeypatch):
        monkeypatch.setattr(core_db, "HOME_OS_DB_PATH", str(db_path))
        version_file = tmp_path / "SCHEMA_VERSION.txt"
        monkeypatch.setattr(core_db, "_SCHEMA_VERSION_FILE", version_file)
        core_db.init_db()
        content = version_file.read_text().strip()
        assert content != ""
        conn = core_db.get_connection()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        assert len(tables) > 0
        conn.close()

    def test_applies_migrations_when_version_behind(self, db_path, tmp_path, monkeypatch):
        monkeypatch.setattr(core_db, "HOME_OS_DB_PATH", str(db_path))
        version_file = tmp_path / "SCHEMA_VERSION.txt"
        migrations = sorted(
            p
            for p in core_db._MIGRATIONS_DIR.iterdir()
            if p.suffix == ".py" and not p.stem.startswith("_")
        )
        if len(migrations) > 1:
            version_file.write_text(migrations[0].name + "\n")
        else:
            version_file.write_text("")
        monkeypatch.setattr(core_db, "_SCHEMA_VERSION_FILE", version_file)
        core_db.init_db()
        content = version_file.read_text().strip()
        assert content != ""
        conn = core_db.get_connection()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        assert len(tables) > 0
        conn.close()

    def test_empty_migrations_dir_is_handled(self, db_path, tmp_path, monkeypatch):
        monkeypatch.setattr(core_db, "HOME_OS_DB_PATH", str(db_path))
        empty_dir = tmp_path / "empty_migrations"
        empty_dir.mkdir()
        monkeypatch.setattr(core_db, "_MIGRATIONS_DIR", empty_dir)
        version_file = tmp_path / "SCHEMA_VERSION.txt"
        monkeypatch.setattr(core_db, "_SCHEMA_VERSION_FILE", version_file)
        core_db.init_db()
        conn = core_db.get_connection()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        assert len(tables) > 0
        conn.close()

    def test_missing_migrations_dir_is_handled(self, db_path, tmp_path, monkeypatch):
        monkeypatch.setattr(core_db, "HOME_OS_DB_PATH", str(db_path))
        missing_dir = tmp_path / "nonexistent_migrations"
        monkeypatch.setattr(core_db, "_MIGRATIONS_DIR", missing_dir)
        version_file = tmp_path / "SCHEMA_VERSION.txt"
        monkeypatch.setattr(core_db, "_SCHEMA_VERSION_FILE", version_file)
        core_db.init_db()
        conn = core_db.get_connection()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        assert len(tables) > 0
        conn.close()
