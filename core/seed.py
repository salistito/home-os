from datetime import date, timedelta
from pathlib import Path

import yaml

from core.db import get_connection, init_db

_SEED_PATH = Path(__file__).parent.parent / "seed" / "tasks.yaml"


def _next_due_date(task: dict, today: date) -> str | None:
    if task.get("frequency_days") is None:
        return None
    return (today + timedelta(days=task.get("start_offset_days", 0))).isoformat()


def load_seed(path: Path | str = _SEED_PATH) -> None:
    data = yaml.safe_load(Path(path).read_text())
    today = date.today()
    with get_connection() as conn:
        for user in data.get("users", []):
            conn.execute(
                "INSERT OR REPLACE INTO users (id, name, telegram_chat_id) "
                "VALUES (?, ?, ?)",
                (user["id"], user["name"], str(user["telegram_chat_id"])),
            )
        for task in data.get("tasks", []):
            if conn.execute(
                "SELECT 1 FROM tasks WHERE name = ?", (task["name"],)
            ).fetchone():
                continue
            conn.execute(
                "INSERT INTO tasks (name, frequency_days, points, next_due_date) "
                "VALUES (?, ?, ?, ?)",
                (
                    task["name"],
                    task.get("frequency_days"),
                    task["points"],
                    _next_due_date(task, today),
                ),
            )


if __name__ == "__main__":
    init_db()
    load_seed()
    print("Seed cargado.")
