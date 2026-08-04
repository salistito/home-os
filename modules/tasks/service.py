from datetime import date

from core.utils.date import get_today, month_key, next_due_date, to_db_date
from modules.tasks import repository
from modules.tasks.assignments_algorithm import (
    BRUTE_FORCE_LIMIT,
    find_greedy_assignment,
    find_optimal_assignment,
)
from modules.tasks.errors import TaskAlreadyExistsError
from modules.tasks.types import (
    Assignment,
    AssignmentCompletionResult,
    AssignmentCompletionStatus,
    TaskOperationResult,
    TaskOperationStatus,
)
from modules.users.repository import get_active_users, get_users


def create_task(
    task_name: str,
    points: int,
    frequency_days: int | None = None,
    next_due_date: str | None = None,
) -> TaskOperationResult:
    task_name = task_name.strip()
    if not task_name:
        return TaskOperationResult(status=TaskOperationStatus.INVALID_NAME)

    if points <= 0:
        return TaskOperationResult(status=TaskOperationStatus.INVALID_POINTS)

    if frequency_days is not None and frequency_days <= 0:
        return TaskOperationResult(status=TaskOperationStatus.INVALID_FREQUENCY)

    try:
        task = repository.create_task(task_name, points, frequency_days, next_due_date)
    except TaskAlreadyExistsError as e:
        return TaskOperationResult(task=e.task, status=TaskOperationStatus.DUPLICATE_NAME)

    return TaskOperationResult(task=task, status=TaskOperationStatus.OK)


def update_active_task(task_id: int, **kwargs: str | int | None) -> TaskOperationResult:
    task = repository.get_active_task_by_id(task_id)
    if task is None:
        return TaskOperationResult(status=TaskOperationStatus.NOT_FOUND)

    if "name" in kwargs:
        new_name = kwargs["name"].strip()
        if not new_name:
            return TaskOperationResult(status=TaskOperationStatus.INVALID_NAME)
        existing = repository.get_active_task_by_name(new_name)
        if existing and existing.id != task_id:
            return TaskOperationResult(task=existing, status=TaskOperationStatus.DUPLICATE_NAME)
        kwargs["name"] = new_name

    if "points" in kwargs and kwargs["points"] <= 0:
        return TaskOperationResult(status=TaskOperationStatus.INVALID_POINTS)

    if "frequency_days" in kwargs:
        if kwargs["frequency_days"] is not None and kwargs["frequency_days"] <= 0:
            return TaskOperationResult(status=TaskOperationStatus.INVALID_FREQUENCY)

    repository.update_active_task(task_id, **kwargs)
    task = repository.get_active_task_by_id(task_id)
    return TaskOperationResult(task=task, status=TaskOperationStatus.OK)


def soft_delete_active_task(task_id: int) -> TaskOperationResult:
    task = repository.get_active_task_by_id(task_id)
    if task is None:
        return TaskOperationResult(status=TaskOperationStatus.NOT_FOUND)

    if repository.task_has_pending_assignments(task_id):
        return TaskOperationResult(task=task, status=TaskOperationStatus.HAS_ASSIGNMENTS)

    repository.soft_delete_active_task(task_id)
    return TaskOperationResult(task=task, status=TaskOperationStatus.OK)


def get_daily_assignments(day: date) -> list[Assignment]:
    existing_assignments = repository.get_day_assignments(day)
    if existing_assignments:
        return existing_assignments

    users = get_active_users()
    if not users:
        return []

    user_ids = [user.id for user in users]
    monthly_points = repository.month_points_by_user(month_key(day))
    current_points = {user_id: monthly_points.get(user_id, 0) for user_id in user_ids}

    due_tasks = sorted(
        repository.get_due_scheduled_tasks(day), key=lambda task: task.points, reverse=True
    )
    if not due_tasks:
        return []

    num_users = len(users)
    num_tasks = len(due_tasks)
    search_space_size = num_users**num_tasks

    if search_space_size <= BRUTE_FORCE_LIMIT:
        assignee_ids = find_optimal_assignment(users, due_tasks, current_points)
    else:
        assignee_ids = find_greedy_assignment(users, due_tasks, current_points)

    assignments = []

    for task, assignee_id in zip(due_tasks, assignee_ids):
        repository.create_assignment(task.id, assignee_id, day)
        assignments.append(Assignment(task.id, task.name, assignee_id, task.points))

    return assignments


def get_pending_daily_assignments(day: date) -> list[Assignment]:
    return repository.get_pending_daily_assignments(day)


def mark_assignment_done(
    text: str, user_id: int, day: date, must_be_assigned_to_user: bool = False
) -> AssignmentCompletionResult:
    task = repository.get_active_task_by_name(text)
    if task is None:
        return AssignmentCompletionResult(status=AssignmentCompletionStatus.NOT_FOUND)
    if repository.get_completed_assignment_id(task.id, day) is not None:
        return AssignmentCompletionResult(
            task_name=task.name, status=AssignmentCompletionStatus.ALREADY_DONE
        )

    scheduled = task.frequency_days is not None
    completed_at = to_db_date(day)

    if scheduled:
        pending = repository.get_pending_assignment(task.id)
        can_complete = pending is not None and (
            pending["user_id"] == user_id or not must_be_assigned_to_user
        )
        if can_complete:
            repository.complete_assignment(pending["id"], user_id, task.points, completed_at)
        elif must_be_assigned_to_user:
            return AssignmentCompletionResult(
                task_name=task.name, status=AssignmentCompletionStatus.NOT_ASSIGNED
            )
        else:
            # pending is None and must_be_assigned_to_user===false.
            repository.create_completed_assignment(task.id, user_id, task.points, day, completed_at)

        repository.set_task_next_due_date(task.id, next_due_date(day, task.frequency_days))
        return AssignmentCompletionResult(
            task_name=task.name,
            status=AssignmentCompletionStatus.OK,
            points_awarded=task.points,
        )
    else:
        repository.create_completed_assignment(task.id, user_id, task.points, day, completed_at)
        return AssignmentCompletionResult(
            task_name=task.name, status=AssignmentCompletionStatus.OK, points_awarded=task.points
        )


def fail_stale_pending_assignments(day: date) -> int:
    return repository.fail_stale_pending_assignments(day)


def get_day_board(day: date) -> dict[int, list[dict]]:
    board: dict[int, list[dict]] = {user.id: [] for user in get_users()}
    for row in repository.get_day_assignment_states(day):
        board.setdefault(row["user_id"], []).append(
            {
                "assignment_id": row["assignment_id"],
                "task_id": row["task_id"],
                "name": row["task_name"],
                "points": row["points"],
                "done": row["status"] == "completed",
            }
        )
    return board


def toggle_assignment(assignment_id: int, user_id: int) -> dict | None:
    assignment = repository.get_assignment_by_id(assignment_id)
    if assignment is None or assignment["user_id"] != user_id:
        return None
    if assignment["status"] not in ("pending", "completed"):
        return None

    today = get_today()

    if assignment["status"] == "completed":
        repository.revert_assignment_by_id(assignment_id)
        if assignment["frequency_days"] is not None:
            repository.set_task_next_due_date(
                assignment["task_id"], assignment["assigned_at"]
            )
        return {"done": False}
    else:
        repository.complete_assignment_by_id(
            assignment_id, to_db_date(today), assignment["points"]
        )
        if assignment["frequency_days"] is not None:
            repository.set_task_next_due_date(
                assignment["task_id"], next_due_date(today, assignment["frequency_days"])
            )
        return {"done": True}


def get_daily_points(month: str) -> dict[str, dict[int, int]]:
    return repository.daily_points_by_user(month)


def get_daily_task_breakdown(month: str) -> dict[str, dict[int, list[dict]]]:
    return repository.daily_task_breakdown_by_user(month)


def get_month_points(month: str) -> dict[int, int]:
    return repository.month_points_by_user(month)
