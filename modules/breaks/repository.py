from core.db import get_connection
from modules.breaks.types import BreakPeriod

_BREAK_PERIOD_COLUMNS = "id, label, start_date, end_date, created_at"

_EDITABLE_BREAK_PERIOD_COLUMNS = {"label", "start_date", "end_date"}


def _row_to_break_period(row) -> BreakPeriod:
    return BreakPeriod(
        row["id"],
        row["label"],
        row["start_date"],
        row["end_date"],
        row["created_at"],
    )


def create_break_period(
    label: str | None,
    start_date: str,
    end_date: str | None,
    created_at: str,
    user_ids: list[int],
) -> BreakPeriod:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO break_periods (label, start_date, end_date, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (label, start_date, end_date, created_at),
        )
        break_period_id = cur.lastrowid
        conn.executemany(
            """
            INSERT INTO break_users (break_period_id, user_id)
            VALUES (?, ?)
            """,
            [(break_period_id, user_id) for user_id in user_ids],
        )
    return get_break_period_by_id(break_period_id)


def _load_break_periods(sql: str = "", params: tuple = ()) -> list[BreakPeriod]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT bp.{_BREAK_PERIOD_COLUMNS}, bu.user_id
            FROM break_periods bp
            LEFT JOIN break_users bu ON bp.id = bu.break_period_id
            {sql}
            ORDER BY bp.start_date DESC, bp.id DESC
            """,
            params,
        ).fetchall()
    break_periods: dict[int, BreakPeriod] = {}
    for row in rows:
        break_period = break_periods.get(row["id"])
        if break_period is None:
            break_period = _row_to_break_period(row)
            break_period.user_ids = []
            break_periods[break_period.id] = break_period
        if row["user_id"] is not None:
            break_period.user_ids.append(row["user_id"])
    return list(break_periods.values())


def get_break_periods() -> list[BreakPeriod]:
    return _load_break_periods()


def get_break_period_by_id(break_period_id: int) -> BreakPeriod | None:
    break_periods = _load_break_periods("WHERE bp.id = ?", (break_period_id,))
    return break_periods[0] if break_periods else None


def get_active_break_period_user_ids(day: str) -> set[int]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT bu.user_id
            FROM break_users bu
            JOIN break_periods bp ON bp.id = bu.break_period_id
            WHERE bp.start_date <= ?
              AND (bp.end_date IS NULL OR bp.end_date >= ?)
            """,
            (day, day),
        ).fetchall()
    return {row["user_id"] for row in rows}


def get_active_break_period_for_user(user_id: int, day: str) -> BreakPeriod | None:
    break_periods = _load_break_periods(
        """
        WHERE bu.user_id = ?
          AND bp.start_date <= ?
          AND (bp.end_date IS NULL OR bp.end_date >= ?)
        """,
        (user_id, day, day),
    )
    return break_periods[0] if break_periods else None


def update_break_period(break_period_id: int, **fields: str | None) -> bool:
    if not fields:
        return True

    invalid = set(fields) - _EDITABLE_BREAK_PERIOD_COLUMNS
    if invalid:
        invalid_names = ", ".join(sorted(invalid))
        raise ValueError(f"Invalid editable break perdios columns: {invalid_names}")

    set_clauses: list[str] = []
    params: list[str | None] = []
    for column, value in fields.items():
        if value is None:
            set_clauses.append(f"{column} = NULL")
        else:
            set_clauses.append(f"{column} = ?")
            params.append(value)
    params.append(break_period_id)

    with get_connection() as conn:
        cur = conn.execute(
            f"""
            UPDATE break_periods
            SET {", ".join(set_clauses)}
            WHERE id = ?
            """,
            params,
        )

    return cur.rowcount > 0


def set_break_period_user_ids(break_period_id: int, user_ids: list[int]) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM break_users WHERE break_period_id = ?",
            (break_period_id,),
        )
        conn.executemany(
            """
            INSERT INTO break_users (break_period_id, user_id)
            VALUES (?, ?)
            """,
            [(break_period_id, user_id) for user_id in user_ids],
        )


def delete_break_period(break_period_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM break_periods WHERE id = ?",
            (break_period_id,),
        )
    return cur.rowcount > 0
