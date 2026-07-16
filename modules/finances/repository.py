import sqlite3

from core.db import get_connection
from modules.finances.errors import OpenPeriodExistsError
from modules.finances.types import Entry, Period

_PERIOD_COLUMNS = "id, label, status, opened_at"
_ENTRY_COLUMNS = (
    "id, period_id, kind, scope, owner_id, label, amount, "
    "status, paid_at, detail_mode, created_at"
)


def _row_to_period(row) -> Period:
    return Period(
        row["id"],
        row["label"],
        row["status"],
        row["opened_at"],
    )


def _row_to_entry(row) -> Entry:
    return Entry(
        row["id"],
        row["period_id"],
        row["kind"],
        row["scope"],
        row["owner_id"],
        row["label"],
        row["amount"],
        row["status"],
        row["paid_at"],
        row["detail_mode"],
        row["created_at"],
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


def create_entry(
    period_id: int,
    kind: str,
    scope: str,
    owner_id: str,
    label: str,
    amount: int,
    created_at: str,
) -> Entry:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO finances_entries
                (period_id, kind, scope, owner_id, label, amount, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (period_id, kind, scope, owner_id, label, amount, created_at),
        )
    return get_entry_by_id(cur.lastrowid)


def set_entry_status(entry_id: int, status: str, paid_at: str | None) -> Entry | None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE finances_entries SET status = ?, paid_at = ? WHERE id = ?",
            (status, paid_at, entry_id),
        )
    return get_entry_by_id(entry_id)


def delete_entry(entry_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM finances_entries WHERE id = ?", (entry_id,))


def get_entry_by_id(entry_id: int) -> Entry | None:
    with get_connection() as conn:
        row = conn.execute(
            f"SELECT {_ENTRY_COLUMNS} FROM finances_entries WHERE id = ?",
            (entry_id,),
        ).fetchone()
    return _row_to_entry(row) if row else None


def get_entries_by_period(period_id: int) -> list[Entry]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_ENTRY_COLUMNS}
            FROM finances_entries
            WHERE period_id = ?
            ORDER BY id
            """,
            (period_id,),
        ).fetchall()
    return [_row_to_entry(r) for r in rows]
