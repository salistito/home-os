import json
import sqlite3
from datetime import date

from core.db import get_connection
from core.utils.date import get_today, to_db_date
from core.utils.string import normalize_string
from modules.tasks.constants import COOK_EVENT_TASK_NAME, COOK_EVENT_TASK_POINTS
from modules.tasks.errors import TaskAlreadyExistsError
from modules.tasks.types import Assignment, Task

_TASK_COLUMNS = "id, name, points, frequency_days, next_due_date"

EDITABLE_TASK_COLUMNS = {
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


def _parse_assignment_source_entity_details(row) -> dict | None:
    data = row["source_entity_details"]
    return json.loads(data) if data else None


def create_task(
    task_name: str,
    points: int,
    frequency_days: int | None,
    next_due_date: str | None = None,
) -> Task:
    normalized_task_name = normalize_string(task_name)
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO tasks (name, points, frequency_days, next_due_date)
                VALUES (?, ?, ?, ?)
                """,
                (normalized_task_name, points, frequency_days, next_due_date),
            )
        return get_active_task_by_id(cur.lastrowid)

    except sqlite3.IntegrityError as e:
        task = get_active_task_by_name(normalized_task_name)
        raise TaskAlreadyExistsError(task) from e


def get_active_task_by_id(task_id: int) -> Task | None:
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


def get_task_by_name(task_name: str) -> Task | None:
    normalized_task_name = normalize_string(task_name)
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_TASK_COLUMNS}
            FROM tasks
            WHERE name = ?
            """,
            (normalized_task_name,),
        ).fetchone()
    return _row_to_task(row) if row else None


def get_active_task_by_name(task_name: str) -> Task | None:
    normalized_task_name = normalize_string(task_name)
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_TASK_COLUMNS}
            FROM tasks
            WHERE name = ?
              AND deleted_at IS NULL
            """,
            (normalized_task_name,),
        ).fetchone()
    return _row_to_task(row) if row else None


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


def get_cooking_task() -> Task:
    cooking_task = get_task_by_name(COOK_EVENT_TASK_NAME)
    if cooking_task is not None:
        return cooking_task
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO tasks (name, points, frequency_days, next_due_date, deleted_at)
            VALUES (?, ?, NULL, NULL, ?)
            """,
            (
                COOK_EVENT_TASK_NAME,
                COOK_EVENT_TASK_POINTS,
                to_db_date(get_today()),
            ),
        )
    return get_task_by_name(COOK_EVENT_TASK_NAME)


def update_active_task(task_id: int, **fields: str | int | None) -> bool:
    if not fields:
        return True

    invalid = set(fields) - EDITABLE_TASK_COLUMNS
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
        task = get_active_task_by_name(normalized_fields["name"])
        assert task is not None
        raise TaskAlreadyExistsError(task) from e


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


def soft_delete_active_task(task_id: int) -> bool:
    deleted_at = to_db_date(get_today())
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM assignments
            WHERE task_id = ?
              AND status = 'pending'
            """,
            (task_id,),
        )
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


def create_assignment(task_id: int, user_id: int, day: date) -> None:
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


def create_completed_assignment(
    task_id: int,
    user_id: int,
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


def create_cooking_assignment(
    task_id: int,
    user_id: int,
    assigned_at: str,
    completed_at: str,
    points_awarded: int,
    source_entity_id: int,
    source_entity_details: dict,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO assignments (
                task_id,
                user_id,
                assigned_at,
                status,
                completed_at,
                points_awarded,
                source,
                source_entity_id,
                source_entity_details
            )
            VALUES (?, ?, ?, 'completed', ?, ?, 'cooking', ?, ?)
            """,
            (
                task_id,
                user_id,
                assigned_at,
                completed_at,
                points_awarded,
                source_entity_id,
                json.dumps(source_entity_details),
            ),
        )


def get_assignment_by_id(assignment_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT a.id, a.task_id, a.user_id, a.assigned_at,
                   a.status, t.points, t.frequency_days,
                   a.source, a.source_entity_id, a.source_entity_details
            FROM assignments a
            JOIN tasks t ON t.id = a.task_id
            WHERE a.id = ?
            """,
            (assignment_id,),
        ).fetchone()
    if row is None:
        return None
    assignment = dict(row)
    assignment["source_entity_details"] = _parse_assignment_source_entity_details(row)
    return assignment


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
              AND a.source = 'task'
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
                a.id AS assignment_id,
                a.task_id,
                t.name AS task_name,
                a.user_id,
                COALESCE(a.points_awarded, t.points) AS points,
                a.status,
                a.source,
                a.source_entity_id,
                a.source_entity_details
            FROM assignments a
            JOIN tasks t
              ON t.id = a.task_id
            WHERE a.assigned_at = ?
            """,
            (assigned_at,),
        ).fetchall()
    assignments = []
    for row in rows:
        assignment = dict(row)
        assignment["source_entity_details"] = _parse_assignment_source_entity_details(row)
        assignments.append(assignment)
    return assignments


def get_pending_daily_assignments(day: date) -> list[Assignment]:
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
              AND a.source = 'task'
            """,
            (assigned_at,),
        ).fetchall()
    return [_row_to_assignment(r) for r in rows]


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


def get_pending_assignment(task_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, task_id, user_id, assigned_at, status, completed_at, points_awarded
            FROM assignments
            WHERE task_id = ?
              AND status = 'pending'
            LIMIT 1
            """,
            (task_id,),
        ).fetchone()
    return dict(row) if row else None


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


def complete_assignment_by_id(assignment_id: int, completed_at: str, points: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE assignments
            SET status = 'completed',
                completed_at = ?,
                points_awarded = ?
            WHERE id = ?
              AND status = 'pending'
            """,
            (completed_at, points, assignment_id),
        )
    return cur.rowcount > 0


def revert_assignment_by_id(assignment_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE assignments
            SET status = 'pending',
                completed_at = NULL,
                points_awarded = NULL
            WHERE id = ?
              AND status = 'completed'
            """,
            (assignment_id,),
        )
    return cur.rowcount > 0


def complete_assignment(
    assignment_id: int,
    user_id: int,
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


def daily_points_by_user(month: str) -> dict[str, dict[int, int]]:
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
    result: dict[str, dict[int, int]] = {}
    for row in rows:
        result.setdefault(row["day"], {})[row["user_id"]] = row["points"]
    return result


def daily_task_breakdown_by_user(month: str) -> dict[str, dict[int, list[dict]]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                a.completed_at AS day,
                a.user_id AS user_id,
                t.name AS task_name,
                a.points_awarded AS points,
                a.source,
                a.source_entity_id,
                a.source_entity_details
            FROM assignments a
            JOIN tasks t
              ON t.id = a.task_id
            WHERE a.status = 'completed'
              AND strftime('%Y-%m', a.completed_at) = ?
            ORDER BY a.completed_at, a.points_awarded DESC, t.name
            """,
            (month,),
        ).fetchall()

    result: dict[str, dict[int, list[dict]]] = {}
    for row in rows:
        day = result.setdefault(row["day"], {})
        task_breakdown = {
            "name": row["task_name"],
            "points": row["points"],
            "source": row["source"],
        }
        if row["source"] != "task":
            task_breakdown["source_entity_id"] = row["source_entity_id"]
            task_breakdown["source_entity_details"] = _parse_assignment_source_entity_details(row)
        day.setdefault(row["user_id"], []).append(task_breakdown)

    return result


def month_points_by_user(month: str) -> dict[int, int]:
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
