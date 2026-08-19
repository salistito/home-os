# tasks

Domain module for household task management.

## Public API

```python
def create_task(task_name: str, points: int, frequency_days: int | None = None, next_due_date: str | None = None) -> TaskOperationResult

def update_active_task(task_id: int, **kwargs: str | int | None) -> TaskOperationResult

def soft_delete_active_task(task_id: int) -> TaskOperationResult

def get_daily_assignments(day: date) -> list[Assignment]

def get_pending_daily_assignments(day: date) -> list[Assignment]

def mark_assignment_done(text: str, user_id: int, day: date, must_be_assigned_to_user: bool = False) -> AssignmentCompletionResult

def fail_stale_pending_assignments(day: date) -> int

def get_day_board(day: date) -> dict[int, list[dict]]

def toggle_assignment(assignment_id: int, user_id: int) -> dict | None

def get_daily_points(month: str) -> dict[str, dict[int, int]]

def get_daily_task_breakdown(month: str) -> dict[str, dict[int, list[dict]]]

def get_month_points(month: str) -> dict[int, int]

def award_cooking_points(user_id: int, portions: int, cooked_at: str, cook_event_id: int, recipe_name: str, recipe_category: str | None = None) -> int
```

## Key types

| Type | Description |
|---|---|
| `Task` | A household chore with points, optional frequency, and next due date |
| `Assignment` | A task assigned to a user for a given day (`task_id`, `task_name`, `user_id`, `points`) |
| `TaskOperationResult` | Result of create/update/delete with `Task | None` and `TaskOperationStatus` |
| `TaskOperationStatus` | Enum: `OK`, `INVALID_NAME`, `INVALID_POINTS`, `INVALID_FREQUENCY`, `DUPLICATE_NAME`, `NOT_FOUND` |
| `AssignmentCompletionResult` | Result of marking an assignment done (`task_name`, `status`, `points_awarded`) |
| `AssignmentCompletionStatus` | Enum: `OK`, `ALREADY_DONE`, `NOT_ASSIGNED`, `NOT_FOUND` |

Cooking assignments are handled through a single `Cocinar` task (2 points) created/used by `get_cooking_task` (repository) and `award_cooking_points` (service).

## Errors

| Error | Description |
|---|---|
| `TaskAlreadyExistsError` | Raised by repository when creating a task with a duplicate active name |
| `TaskNotFoundError` | Raised when a task is not found by id |

## Dependencies

- `core/` for DB connection, date utilities, and string utilities
- Does NOT import from `apps/`