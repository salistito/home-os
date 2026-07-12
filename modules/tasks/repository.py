import sqlite3

from datetime import date

from core.db import get_connection
from core.utils.date import get_today, to_db_date
from core.utils.string import normalize_string
from modules.tasks.errors import TaskAlreadyExistsError
from modules.tasks.types import Assignment, Task

_TASK_COLUMNS = "id, name, points, frequency_days, next_due_date"

_EDITABLE_TASK_COLUMNS = {
    "name",
    "points",
    "frequency_days",
    "next_due_date",
}


def _row_to_task(row) -> Task:
    return Task(
        row["id"],
        row["name"],
        row["points"],
        row["frequency_days"],
        row["next_due_date"],
    )


def _row_to_assignment(row) -> Assignment:
    return Assignment(
        row["task_id"],
        row["task_name"],
        row["user_id"],
        row["points"],
    )


def create_task(
    task_name: str,
    points: int,
    frequency_days: int | None,
    next_due_date: str | None = None,
) -> int:
    normalized_name = normalize_string(task_name)
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO tasks (name, points, frequency_days, next_due_date)
                VALUES (?, ?, ?, ?)
                """,
                (normalized_name, points, frequency_days, next_due_date),
            )

        return cur.lastrowid

    except sqlite3.IntegrityError as e:
        task = find_active_task_by_name(normalized_name)
        raise TaskAlreadyExistsError(task) from e


def get_active_tasks() -> list[Task]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_TASK_COLUMNS}
            FROM tasks
            WHERE deleted_at IS NULL
            ORDER BY name
            """
        ).fetchall()

    return [_row_to_task(r) for r in rows]


def find_active_task_by_id(task_id: int) -> Task | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_TASK_COLUMNS}
            FROM tasks
            WHERE id = ?
              AND deleted_at IS NULL
            """,
            (task_id,),
        ).fetchone()

    return _row_to_task(row) if row else None


def find_active_task_by_name(task_name: str) -> Task | None:
    normalized_name = normalize_string(task_name)
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_TASK_COLUMNS}
            FROM tasks
            WHERE name = ?
              AND deleted_at IS NULL
            """,
            (normalized_name,),
        ).fetchone()

    return _row_to_task(row) if row else None


def get_due_scheduled_tasks(day: date) -> list[Task]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_TASK_COLUMNS}
            FROM tasks
            WHERE frequency_days IS NOT NULL
              AND next_due_date IS NOT NULL
              AND next_due_date <= ?
              AND deleted_at IS NULL
            ORDER BY next_due_date, name
            """,
            (to_db_date(day),),
        ).fetchall()

    return [_row_to_task(r) for r in rows]


def update_active_task(task_id: int, **fields: str | int | None) -> bool:
    if not fields:
        return True

    invalid = set(fields) - _EDITABLE_TASK_COLUMNS
    if invalid:
        raise ValueError(f"Invalid editable task columns: {', '.join(sorted(invalid))}")

    normalized_fields = fields.copy()

    if "name" in normalized_fields and normalized_fields["name"] is not None:
        normalized_fields["name"] = normalize_string(normalized_fields["name"])

    set_clauses: list[str] = []
    params: list[str | int] = []

    for column, value in normalized_fields.items():
        if value is None:
            set_clauses.append(f"{column} = NULL")
        else:
            set_clauses.append(f"{column} = ?")
            params.append(value)

    params.append(task_id)

    try:
        with get_connection() as conn:
            cur = conn.execute(
                f"""
                UPDATE tasks
                SET {", ".join(set_clauses)}
                WHERE id = ?
                  AND deleted_at IS NULL
                """,
                params,
            )

        return cur.rowcount > 0

    except sqlite3.IntegrityError as e:
        task = find_active_task_by_name(normalized_fields["name"])
        assert task is not None
        raise TaskAlreadyExistsError(task) from e


def soft_delete_active_task(task_id: int) -> bool:
    deleted_at = to_db_date(get_today())
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE tasks
            SET deleted_at = ?
            WHERE id = ?
              AND deleted_at IS NULL
            """,
            (deleted_at, task_id),
        )

    return cur.rowcount > 0


def task_has_pending_assignments(task_id: int) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT 1
            FROM assignments
            WHERE task_id = ?
              AND status = 'pending'
            LIMIT 1
            """,
            (task_id,),
        ).fetchone()

    return row is not None


def get_day_assignments(day: date) -> list[Assignment]:
    assigned_at = to_db_date(day)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                a.task_id,
                t.name AS task_name,
                a.user_id,
                t.points
            FROM assignments a
            JOIN tasks t
              ON t.id = a.task_id
            WHERE a.assigned_at = ?
            """,
            (assigned_at,),
        ).fetchall()

    return [_row_to_assignment(r) for r in rows]


def get_day_assignment_states(day: date) -> list[dict]:
    assigned_at = to_db_date(day)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                a.task_id,
                t.name AS task_name,
                a.user_id,
                t.points,
                a.status
            FROM assignments a
            JOIN tasks t
              ON t.id = a.task_id
            WHERE a.assigned_at = ?
            """,
            (assigned_at,),
        ).fetchall()

    return [dict(r) for r in rows]


def get_pending_day_assignments(day: date) -> list[Assignment]:
    assigned_at = to_db_date(day)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                a.task_id,
                t.name AS task_name,
                a.user_id,
                t.points
            FROM assignments a
            JOIN tasks t
              ON t.id = a.task_id
            WHERE a.assigned_at = ?
              AND a.status = 'pending'
            """,
            (assigned_at,),
        ).fetchall()

    return [_row_to_assignment(r) for r in rows]


def create_assignment(task_id: int, user_id: str, day: date) -> None:
    assigned_at = to_db_date(day)
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO assignments (
                task_id,
                user_id,
                assigned_at,
                status
            )
            VALUES (?, ?, ?, 'pending')
            """,
            (task_id, user_id, assigned_at),
        )


def get_pending_assignment_id(task_id: int) -> int | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id
            FROM assignments
            WHERE task_id = ?
              AND status = 'pending'
            LIMIT 1
            """,
            (task_id,),
        ).fetchone()

    return row["id"] if row else None


def get_completed_assignment_id(task_id: int, day: date) -> int | None:
    assigned_at = to_db_date(day)
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id
            FROM assignments
            WHERE task_id = ?
              AND assigned_at = ?
              AND status = 'completed'
            LIMIT 1
            """,
            (task_id, assigned_at),
        ).fetchone()

    return row["id"] if row else None


def complete_assignment(
    assignment_id: int,
    user_id: str,
    points: int,
    completed_at: str,
) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE assignments
            SET user_id = ?,
                status = 'completed',
                completed_at = ?,
                points_awarded = ?
            WHERE id = ?
              AND status = 'pending'
            """,
            (user_id, completed_at, points, assignment_id),
        )

    return cur.rowcount > 0


def create_completed_assignment(
    task_id: int,
    user_id: str,
    points: int,
    day: date,
    completed_at: str,
) -> None:
    assigned_at = to_db_date(day)
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO assignments (
                task_id,
                user_id,
                assigned_at,
                status,
                completed_at,
                points_awarded
            )
            VALUES (?, ?, ?, 'completed', ?, ?)
            """,
            (task_id, user_id, assigned_at, completed_at, points),
        )


def set_task_next_due_date(task_id: int, next_due_date: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE tasks
            SET next_due_date = ?
            WHERE id = ?
              AND deleted_at IS NULL
            """,
            (next_due_date, task_id),
        )

    return cur.rowcount > 0


def fail_stale_pending_assignments(day: date) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE assignments
            SET status = 'failed'
            WHERE status = 'pending'
              AND assigned_at < ?
            """,
            (to_db_date(day),),
        )

    return cur.rowcount


def month_points_by_user(month: str) -> dict[str, int]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                u.id AS user_id,
                COALESCE(SUM(a.points_awarded), 0) AS points
            FROM users u
            LEFT JOIN assignments a
                ON a.user_id = u.id
                AND a.status = 'completed'
                AND strftime('%Y-%m', a.completed_at) = ?
            GROUP BY u.id
            """,
            (month,),
        ).fetchall()

    return {row["user_id"]: row["points"] for row in rows}


def daily_points_by_user(month: str) -> dict[str, dict[str, int]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                a.completed_at AS day,
                a.user_id AS user_id,
                COALESCE(SUM(a.points_awarded), 0) AS points
            FROM assignments a
            WHERE a.status = 'completed'
              AND strftime('%Y-%m', a.completed_at) = ?
            GROUP BY a.completed_at, a.user_id
            ORDER BY a.completed_at
            """,
            (month,),
        ).fetchall()

    result: dict[str, dict[str, int]] = {}
    for row in rows:
        result.setdefault(row["day"], {})[row["user_id"]] = row["points"]

    return result
