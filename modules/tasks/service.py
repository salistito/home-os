from datetime import UTC, date, datetime, timedelta

from core.identity import get_users
from modules.tasks import repository
from modules.tasks.types import Assignment, MarkTaskResult, MarkTaskStatus


def get_daily_assignments(day: date) -> list[Assignment]:
    return [
        Assignment(1, "Lavar loza", "antonia", 3),
        Assignment(2, "Limpiar baño", "sebastian", 8),
    ]


def mark_task_done(text: str, user_id: str, day: date) -> MarkTaskResult:
    matches = repository.find_tasks_by_name_in_text(text)
    if len(matches) != 1:
        return MarkTaskResult(MarkTaskStatus.NOT_FOUND, None, 0)

    task = matches[0]
    if repository.get_completed_assignment_id(task.id, day) is not None:
        return MarkTaskResult(MarkTaskStatus.ALREADY_DONE, task.name, 0)

    completed_at = datetime.now(UTC).isoformat()
    scheduled = task.frequency_days is not None

    pending_id = repository.get_pending_assignment_id(task.id) if scheduled else None
    if pending_id is None:
        repository.create_completed_assignment(
            task.id, user_id, task.points, day, completed_at
        )
    else:
        repository.complete_assignment(pending_id, user_id, task.points, completed_at)

    if scheduled:
        next_due = (day + timedelta(days=task.frequency_days)).isoformat()
        repository.set_next_due_date(task.id, next_due)

    return MarkTaskResult(MarkTaskStatus.OK, task.name, task.points)


def get_month_balance(month: str) -> dict[str, int]:
    points = repository.month_points_by_user(month)
    return {user.id: points.get(user.id, 0) for user in get_users()}
