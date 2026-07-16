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


def _amount_is_not_null(conn: sqlite3.Connection) -> bool:
    rows = conn.execute("PRAGMA table_info(finances_entries)").fetchall()
    amount = next((row for row in rows if row["name"] == "amount"), None)
    return amount is not None and amount["notnull"] == 1


def _make_finances_amount_nullable(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA foreign_keys=OFF;
        CREATE TABLE finances_entries_new (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          period_id   INTEGER NOT NULL,
          kind        TEXT NOT NULL CHECK (kind IN ('income', 'expense')),
          scope       TEXT NOT NULL CHECK (scope IN ('shared', 'personal')),
          owner_id    TEXT NOT NULL,
          label       TEXT NOT NULL,
          amount      INTEGER,
          status      TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'confirmed')),
          paid_at     TEXT,
          detail_mode TEXT NOT NULL DEFAULT 'none'
                        CHECK (detail_mode IN ('none', 'top_down', 'bottom_up')),
          created_at  TEXT NOT NULL,
          FOREIGN KEY (period_id) REFERENCES finances_periods(id),
          FOREIGN KEY (owner_id)  REFERENCES users(id)
        );
        INSERT INTO finances_entries_new SELECT * FROM finances_entries;
        DROP TABLE finances_entries;
        ALTER TABLE finances_entries_new RENAME TO finances_entries;
        CREATE INDEX IF NOT EXISTS idx_finances_entries_period
        ON finances_entries(period_id);
        PRAGMA foreign_keys=ON;
        """
    )


def _migrate(conn: sqlite3.Connection) -> None:
    if not _column_exists(conn, "users", "password_hash"):
        conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    if _amount_is_not_null(conn):
        _make_finances_amount_nullable(conn)


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(_SCHEMA.read_text(encoding="utf-8"))
        _migrate(conn)
