import random
from datetime import UTC, date, datetime, timedelta

from core.identity import get_users
from modules.tasks import repository
from modules.tasks.types import Assignment, MarkTaskResult, MarkTaskStatus

DAILY_CAP_MULTIPLIER = 1.5


def calculate_daily_cap(max_points: int) -> int:
    return int(max_points * DAILY_CAP_MULTIPLIER)


def clear_stale_pending(day: date) -> int:
    return repository.fail_stale_pending(day)


def get_daily_assignments(day: date) -> list[Assignment]:
    assignments = repository.get_day_assignments(day)
    if assignments:
        return assignments

    users = get_users()
    projected_points = repository.month_points_by_user(day.strftime("%Y-%m"))
    for user in users:
        projected_points.setdefault(user.id, 0)

    due_tasks = sorted(
        repository.get_due_scheduled_tasks(day), key=lambda t: t.points, reverse=True
    )
    if not due_tasks:
        return []

    assignments = []
    today_points = {u.id: 0 for u in users}
    daily_cap = calculate_daily_cap(due_tasks[0].points)

    for task in due_tasks:
        eligible = [u for u in users if today_points[u.id] + task.points <= daily_cap]
        if not eligible:
            continue

        min_projected = min(projected_points[u.id] for u in eligible)
        tied = [u for u in eligible if projected_points[u.id] == min_projected]
        assignee = random.choice(tied)

        repository.create_assignment(task.id, assignee.id, day)
        projected_points[assignee.id] += task.points
        today_points[assignee.id] += task.points
        assignments.append(Assignment(task.id, task.name, assignee.id, task.points))

    return assignments


def get_pending_assignments(day: date) -> list[Assignment]:
    return repository.get_pending_day_assignments(day)


def mark_task_done(text: str, user_id: str, day: date) -> MarkTaskResult:
    matches = repository.find_tasks_by_name(text)
    if len(matches) != 1:
        return MarkTaskResult(MarkTaskStatus.NOT_FOUND, None, 0)

    task = matches[0]
    if repository.get_completed_assignment_id(task.id, day) is not None:
        return MarkTaskResult(MarkTaskStatus.ALREADY_DONE, task.name, 0)

    completed_at = datetime.now(UTC).isoformat()
    scheduled = task.frequency_days is not None

    pending_id = repository.get_pending_assignment_id(task.id) if scheduled else None
    if pending_id is None:
        repository.create_completed_assignment(task.id, user_id, task.points, day, completed_at)
    else:
        repository.complete_assignment(pending_id, user_id, task.points, completed_at)

    if scheduled:
        next_due = (day + timedelta(days=task.frequency_days)).isoformat()
        repository.set_next_due_date(task.id, next_due)

    return MarkTaskResult(MarkTaskStatus.OK, task.name, task.points)


def get_month_balance(month: str) -> dict[str, int]:
    points = repository.month_points_by_user(month)
    return {user.id: points.get(user.id, 0) for user in get_users()}
