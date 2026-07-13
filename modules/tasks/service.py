import random

from datetime import date

from core.identity import get_users
from core.utils.date import month_key, next_due_date, to_db_date
from modules.tasks import repository
from modules.tasks.errors import TaskAlreadyExistsError
from modules.tasks.types import (
    Assignment,
    AssignmentCompletionResult,
    AssignmentCompletionStatus,
    TaskOperationResult,
    TaskOperationStatus,
)

DAILY_CAP_MULTIPLIER = 1.5  # TODO: Review if this works fine with tasks with small amount of points


def _calculate_daily_cap(max_points: int) -> int:
    return int(max_points * DAILY_CAP_MULTIPLIER)


def create_task(
    task_name: str,
    points: int,
    frequency_days: int | None = None,
    next_due_date: str | None = None,
) -> TaskOperationResult:
    task_name = task_name.strip()
    if not task_name:
        return TaskOperationResult(None, TaskOperationStatus.INVALID_NAME)

    if points <= 0:
        return TaskOperationResult(None, TaskOperationStatus.INVALID_POINTS)

    if frequency_days is not None and frequency_days <= 0:
        return TaskOperationResult(None, TaskOperationStatus.INVALID_FREQUENCY)

    try:
        task_id = repository.create_task(task_name, points, frequency_days, next_due_date)
    except TaskAlreadyExistsError as e:
        return TaskOperationResult(e.task, TaskOperationStatus.DUPLICATE_NAME)

    task = repository.get_active_task_by_id(task_id)
    return TaskOperationResult(task, TaskOperationStatus.OK)


def update_active_task(task_id: int, **kwargs: str | int | None) -> TaskOperationResult:
    task = repository.get_active_task_by_id(task_id)
    if task is None:
        return TaskOperationResult(None, TaskOperationStatus.NOT_FOUND)

    if "name" in kwargs:
        new_name = kwargs["name"].strip()
        if not new_name:
            return TaskOperationResult(None, TaskOperationStatus.INVALID_NAME)
        existing = repository.get_active_task_by_name(new_name)
        if existing and existing.id != task_id:
            return TaskOperationResult(existing, TaskOperationStatus.DUPLICATE_NAME)
        kwargs["name"] = new_name

    if "points" in kwargs and kwargs["points"] <= 0:
        return TaskOperationResult(None, TaskOperationStatus.INVALID_POINTS)

    if "frequency_days" in kwargs:
        if kwargs["frequency_days"] is not None and kwargs["frequency_days"] <= 0:
            return TaskOperationResult(None, TaskOperationStatus.INVALID_FREQUENCY)

    repository.update_active_task(task_id, **kwargs)
    task = repository.get_active_task_by_id(task_id)
    return TaskOperationResult(task, TaskOperationStatus.OK)


def soft_delete_active_task(task_id: int) -> TaskOperationResult:
    task = repository.get_active_task_by_id(task_id)
    if task is None:
        return TaskOperationResult(None, TaskOperationStatus.NOT_FOUND)

    if repository.task_has_pending_assignments(task_id):
        return TaskOperationResult(task, TaskOperationStatus.HAS_ASSIGNMENTS)

    repository.soft_delete_active_task(task_id)
    return TaskOperationResult(task, TaskOperationStatus.OK)


def get_daily_assignments(day: date) -> list[Assignment]:
    assignments = repository.get_day_assignments(day)
    if assignments:
        return assignments

    users = get_users()
    projected_points = repository.month_points_by_user(month_key(day))
    for user in users:
        projected_points.setdefault(user.id, 0)

    due_tasks = sorted(
        repository.get_due_scheduled_tasks(day), key=lambda t: t.points, reverse=True
    )
    if not due_tasks:
        return []

    assignments = []
    today_points = {u.id: 0 for u in users}
    daily_cap = _calculate_daily_cap(due_tasks[0].points)

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


def get_pending_daily_assignments(day: date) -> list[Assignment]:
    return repository.get_pending_daily_assignments(day)


def mark_assignment_done(text: str, user_id: str, day: date) -> AssignmentCompletionResult:
    task = repository.get_active_task_by_name(text)
    if task is None:
        return AssignmentCompletionResult(None, AssignmentCompletionStatus.NOT_FOUND, 0)
    if repository.get_completed_assignment_id(task.id, day) is not None:
        return AssignmentCompletionResult(task.name, AssignmentCompletionStatus.ALREADY_DONE, 0)

    completed_at = to_db_date(day)
    scheduled = task.frequency_days is not None

    pending_id = repository.get_pending_assignment_id(task.id) if scheduled else None
    if pending_id is None:
        repository.create_completed_assignment(
            task.id,
            user_id,
            task.points,
            day,
            completed_at,
        )
    else:
        repository.complete_assignment(pending_id, user_id, task.points, completed_at)

    if scheduled:
        next_due = next_due_date(day, task.frequency_days)
        repository.set_task_next_due_date(task.id, next_due)

    return AssignmentCompletionResult(task.name, AssignmentCompletionStatus.OK, task.points)


def fail_stale_pending_assignments(day: date) -> int:
    return repository.fail_stale_pending_assignments(day)


def get_month_balance(month: str) -> dict[str, int]:
    points = repository.month_points_by_user(month)
    return {user.id: points.get(user.id, 0) for user in get_users()}


def get_daily_balance(month: str) -> dict[str, dict[str, int]]:
    daily = repository.daily_points_by_user(month)
    return {
        day: {user.id: points.get(user.id, 0) for user in get_users()}
        for day, points in daily.items()
    }


def get_daily_task_breakdown(month: str) -> dict[str, dict[str, list[dict]]]:
    return repository.daily_task_breakdown_by_user(month)


def get_day_board(day: date) -> dict[str, list[dict]]:
    board: dict[str, list[dict]] = {user.id: [] for user in get_users()}
    for row in repository.get_day_assignment_states(day):
        board.setdefault(row["user_id"], []).append(
            {
                "task_id": row["task_id"],
                "name": row["task_name"],
                "points": row["points"],
                "done": row["status"] == "completed",
            }
        )
    return board
