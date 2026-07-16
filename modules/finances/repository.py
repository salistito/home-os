import sqlite3

from core.db import get_connection
from modules.finances.errors import OpenPeriodExistsError
from modules.finances.types import Period

_PERIOD_COLUMNS = "id, label, status, opened_at"


def _row_to_period(row) -> Period:
    return Period(
        row["id"],
        row["label"],
        row["status"],
        row["opened_at"],
    )


def create_period(label: str, opened_at: str) -> Period:
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO finances_periods (label, status, opened_at)
                VALUES (?, 'open', ?)
                """,
                (label, opened_at),
            )
        return get_period_by_id(cur.lastrowid)

    except sqlite3.IntegrityError as e:
        open_period = get_open_period()
        raise OpenPeriodExistsError(open_period) from e


def close_open_period() -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE finances_periods SET status = 'closed' WHERE status = 'open'"
        )


def get_open_period() -> Period | None:
    with get_connection() as conn:
        row = conn.execute(
            f"SELECT {_PERIOD_COLUMNS} FROM finances_periods WHERE status = 'open'"
        ).fetchone()
    return _row_to_period(row) if row else None


def get_period_by_id(period_id: int) -> Period | None:
    with get_connection() as conn:
        row = conn.execute(
            f"SELECT {_PERIOD_COLUMNS} FROM finances_periods WHERE id = ?",
            (period_id,),
        ).fetchone()
    return _row_to_period(row) if row else None


def get_period_by_label(label: str) -> Period | None:
    with get_connection() as conn:
        row = conn.execute(
            f"SELECT {_PERIOD_COLUMNS} FROM finances_periods WHERE label = ?",
            (label,),
        ).fetchone()
    return _row_to_period(row) if row else None


def get_periods() -> list[Period]:
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT {_PERIOD_COLUMNS} FROM finances_periods ORDER BY id DESC"
        ).fetchall()
    return [_row_to_period(r) for r in rows]
