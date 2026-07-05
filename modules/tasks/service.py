from datetime import date

from core.identity import get_users
from modules.tasks import repository
from modules.tasks.types import Assignment, MarkTaskResult, MarkTaskStatus


def get_daily_assignments(day: date) -> list[Assignment]:
    return [
        Assignment(1, "Lavar loza", "antonia", 3),
        Assignment(2, "Limpiar baño", "sebastian", 8),
    ]


def mark_task_done(text: str, user_id: str, day: date) -> MarkTaskResult:
    return MarkTaskResult(MarkTaskStatus.OK, "Lavar loza", 3)


def get_month_balance(month: str) -> dict[str, int]:
    points = repository.month_points_by_user(month)
    return {user.id: points.get(user.id, 0) for user in get_users()}
