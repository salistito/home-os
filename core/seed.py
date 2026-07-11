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


def _next_due_date(task: dict, today: date) -> str | None:
    if task.get("frequency_days") is None:
        return None
    return next_due_date(today, task.get("start_offset_days", 0))


def _load_yaml(path: Path | str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def load_seed() -> None:
    users_data = _load_yaml(_USERS_SEED_PATH)
    tasks_data = _load_yaml(_TASKS_SEED_PATH)
    today = get_today()
    with get_connection() as conn:
        for user in users_data.get("users", []):
            conn.execute(
                "INSERT OR REPLACE INTO users (id, name, telegram_chat_id) VALUES (?, ?, ?)",
                (
                    user["id"],
                    user["name"],
                    os.path.expandvars(str(user["telegram_chat_id"])),
                ),
            )
        for task in tasks_data.get("tasks", []):
            if conn.execute(
                "SELECT 1 FROM tasks WHERE lower(name) = lower(?)", (task["name"],)
            ).fetchone():
                continue
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


if __name__ == "__main__":
    init_db()
    load_seed()
    print("Seed cargado.")
