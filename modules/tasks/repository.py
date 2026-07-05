from datetime import date

from core.db import get_connection
from modules.tasks.types import Assignment, Task

_TASK_COLUMNS = "id, name, frequency_days, points, next_due_date"


def _task(row) -> Task:
    return Task(
        row["id"],
        row["name"],
        row["frequency_days"],
        row["points"],
        row["next_due_date"],
    )


def get_tasks() -> list[Task]:
    with get_connection() as conn:
        rows = conn.execute(f"SELECT {_TASK_COLUMNS} FROM tasks").fetchall()
    return [_task(r) for r in rows]


def get_due_scheduled_tasks(day: date) -> list[Task]:
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT {_TASK_COLUMNS} FROM tasks "
            "WHERE frequency_days IS NOT NULL AND next_due_date IS NOT NULL "
            "AND next_due_date <= ?",
            (day.isoformat(),),
        ).fetchall()
    return [_task(r) for r in rows]


def find_tasks_by_name_in_text(text: str) -> list[Task]:
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT {_TASK_COLUMNS} FROM tasks WHERE instr(lower(?), lower(name)) > 0",
            (text,),
        ).fetchall()
    return [_task(r) for r in rows]


def get_day_assignments(day: date) -> list[Assignment]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT a.task_id, t.name AS task_name, a.user_id, t.points "
            "FROM assignments a JOIN tasks t ON t.id = a.task_id "
            "WHERE a.assigned_at = ?",
            (day.isoformat(),),
        ).fetchall()
    return [
        Assignment(r["task_id"], r["task_name"], r["user_id"], r["points"])
        for r in rows
    ]


def create_assignment(task_id: int, user_id: str, day: date) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO assignments (task_id, user_id, assigned_at, status) "
            "VALUES (?, ?, ?, 'pending')",
            (task_id, user_id, day.isoformat()),
        )


def fail_stale_pending(before: date) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE assignments SET status = 'failed' "
            "WHERE status = 'pending' AND assigned_at < ?",
            (before.isoformat(),),
        )
        return cur.rowcount


def month_points_by_user(month: str) -> dict[str, int]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT user_id, SUM(points_awarded) AS points FROM assignments "
            "WHERE status = 'completed' AND substr(completed_at, 1, 7) = ? "
            "GROUP BY user_id",
            (month,),
        ).fetchall()
    return {r["user_id"]: r["points"] for r in rows}
