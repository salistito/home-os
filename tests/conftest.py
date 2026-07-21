import pytest


@pytest.fixture
def db_path(monkeypatch, tmp_path):
    db_file = tmp_path / "test_homeos.db"
    monkeypatch.setattr("core.db.HOME_OS_DB_PATH", str(db_file))
    return db_file


@pytest.fixture
def jwt_secret(monkeypatch):
    secret = "a-test-jwt-secret-that-is-at-least-32-bytes-long"
    monkeypatch.setattr("core.config.JWT_SECRET", secret)
    return secret


@pytest.fixture
def db(db_path):
    from core.db import init_db, get_connection
    init_db()
    conn = get_connection()
    yield conn
    conn.close()


@pytest.fixture
def db_user(db):
    from modules.users.repository import create_user
    return create_user("Test User", role="admin")


@pytest.fixture
def db_second_user(db):
    from modules.users.repository import create_user
    return create_user("Second User", role="member")


@pytest.fixture
def frozen_now(monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    fixed = datetime(2026, 3, 15, 10, 30, 0, tzinfo=ZoneInfo("America/Santiago"))

    def mock_get_now():
        return fixed

    monkeypatch.setattr("core.utils.date.get_now", mock_get_now)
    return fixed


@pytest.fixture
def frozen_today(monkeypatch):
    from datetime import date

    fixed = date(2026, 3, 15)

    def mock_get_today():
        return fixed

    monkeypatch.setattr("core.utils.date.get_today", mock_get_today)
    return fixed


@pytest.fixture
def frozen_now_utc(monkeypatch):
    from datetime import datetime, timezone

    fixed = datetime(2026, 3, 15, 14, 30, 0, tzinfo=timezone.utc)

    def mock_get_now_utc():
        return fixed

    monkeypatch.setattr("core.utils.date.get_now_utc", mock_get_now_utc)
    return fixed
