from datetime import date

from modules.tasks.types import Assignment, MarkTaskResult


def get_daily_assignments(day: date) -> list[Assignment]:
    raise NotImplementedError


def mark_task_done(text: str, user_id: str, day: date) -> MarkTaskResult:
    raise NotImplementedError


def get_month_balance(month: str) -> dict[str, int]:
    raise NotImplementedError
