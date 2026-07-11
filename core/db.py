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


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(_SCHEMA.read_text(encoding="utf-8"))
