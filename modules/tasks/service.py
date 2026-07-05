from datetime import date

from modules.tasks.types import Assignment, MarkTaskResult, MarkTaskStatus


def get_daily_assignments(day: date) -> list[Assignment]:
    return [
        Assignment(1, "Lavar loza", "antonia", 3),
        Assignment(2, "Limpiar baño", "sebastian", 8),
    ]


def mark_task_done(text: str, user_id: str, day: date) -> MarkTaskResult:
    return MarkTaskResult(MarkTaskStatus.OK, "Lavar loza", 3)


def get_month_balance(month: str) -> dict[str, int]:
    return {"antonia": 40, "sebastian": 38}
