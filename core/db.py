import sqlite3
from pathlib import Path

from core.config import HOME_OS_DB_PATH

_SCHEMA = Path(__file__).parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    Path(HOME_OS_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(HOME_OS_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row["name"] == column for row in rows)


def _migrate(conn: sqlite3.Connection) -> None:
    if not _column_exists(conn, "users", "password_hash"):
        conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(_SCHEMA.read_text(encoding="utf-8"))
        _migrate(conn)
