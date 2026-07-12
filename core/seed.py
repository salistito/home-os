import os
import yaml
from datetime import date
from pathlib import Path

import core.config  # noqa: F401  (loads .env)
from core.db import get_connection, init_db
from core.utils.date import get_today, next_due_date
from core.utils.string import normalize_string

_USERS_SEED_PATH = Path(__file__).parent.parent / "seed" / "users.yaml"
_TASKS_SEED_PATH = Path(__file__).parent.parent / "seed" / "tasks.yaml"
_ASSIGNMENTS_SEED_PATH = Path(__file__).parent.parent / "seed" / "assignments.yaml"


def _load_yaml(path: Path | str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def _next_due_date(task: dict, today: date) -> str | None:
    if task.get("frequency_days") is None:
        return None
    if "next_due_date" in task:
        return str(task["next_due_date"])
    return next_due_date(today, task.get("start_offset_days", 0))


def load_seed() -> None:
    users_data = _load_yaml(_USERS_SEED_PATH)
    tasks_data = _load_yaml(_TASKS_SEED_PATH)
    assignments_data = _load_yaml(_ASSIGNMENTS_SEED_PATH)
    today = get_today()
    with get_connection() as conn:
        for user in users_data.get("users", []):
            conn.execute(
                "INSERT INTO users (id, name, telegram_chat_id) VALUES (?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "name = excluded.name, telegram_chat_id = excluded.telegram_chat_id",
                (
                    user["id"],
                    user["name"],
                    os.path.expandvars(str(user["telegram_chat_id"])),
                ),
            )

        has_tasks = conn.execute("SELECT 1 FROM tasks LIMIT 1").fetchone()
        if not has_tasks:
            for task in tasks_data.get("tasks", []):
                conn.execute(
                    "INSERT INTO tasks (name, points, frequency_days, next_due_date) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        normalize_string(task["name"]),
                        task["points"],
                        task.get("frequency_days"),
                        _next_due_date(task, today),
                    ),
                )

        has_assignments = conn.execute("SELECT 1 FROM assignments LIMIT 1").fetchone()
        if not has_assignments:
            task_ids = {
                row["name"]: row["id"]
                for row in conn.execute("SELECT id, name FROM tasks").fetchall()
            }
            user_ids = {
                row["name"]: row["id"]
                for row in conn.execute("SELECT id, name FROM users").fetchall()
            }
            for a in assignments_data.get("assignments", []):
                task_id = task_ids.get(normalize_string(a["task_name"]))
                user_id = user_ids.get(a["user_name"])
                if task_id is None or user_id is None:
                    continue
                conn.execute(
                    "INSERT INTO assignments "
                    "(task_id, user_id, assigned_at, status, completed_at, points_awarded) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        task_id,
                        user_id,
                        a["assigned_at"],
                        a["status"],
                        a.get("completed_at"),
                        a.get("points_awarded"),
                    ),
                )


if __name__ == "__main__":
    init_db()
    load_seed()
    print("Seed cargado.")
