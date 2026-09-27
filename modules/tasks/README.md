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

def award_cooking_points(user_id: int, portions: int, cooked_at: str, cook_event_id: int, recipe_name: str, recipe_category: str | None = None, recipe_points_awarded: int | None = None, recipe_points_min_portions: int | None = None) -> int

def fail_stale_pending_assignments(day: date) -> int

def fail_break_period_pending_assignments(day: date) -> int

def get_day_board(day: date) -> dict[int, list[dict]]

def toggle_assignment(assignment_id: int, user_id: int) -> dict | None

def get_daily_points(month: str) -> dict[str, dict[int, int]]

def get_daily_task_breakdown(month: str) -> dict[str, dict[int, list[dict]]]

def get_month_points(month: str) -> dict[int, int]
```

## Key types

| Type | Description |
|---|---|
| `Task` | A household chore with points, optional frequency, and next due date |
| `Assignment` | A task assigned to a user for a given day (`task_id`, `task_name`, `user_id`, `points`) |
| `TaskOperationResult` | Result of create/update/delete with `Task | None` and `TaskOperationStatus` |
| `TaskOperationStatus` | Enum: `OK`, `INVALID_NAME`, `INVALID_POINTS`, `INVALID_FREQUENCY`, `DUPLICATE_NAME`, `NOT_FOUND` |
| `AssignmentCompletionResult` | Result of marking an assignment done (`task_name`, `status`, `points_awarded`) |
| `AssignmentCompletionStatus` | Enum: `OK`, `ALREADY_DONE`, `NOT_ASSIGNED`, `ON_BREAK_PERIOD`, `NOT_FOUND` |

Cooking assignments are handled through a single `Cocinar` system task (0 points) managed by `get_cooking_task` (repository) and `award_cooking_points` (service). The task row is created soft-deleted (`deleted_at` set) so it never appears in active task listings nor joins the daily rotation; `get_cooking_task` finds it by name regardless of its deleted state and reuses the same row. Points for cooking come from the recipe's own config: `award_cooking_points` creates a completed cooking assignment worth `points_awarded` only when `portions >= COALESCE(points_min_portions, 1)`; recipes without `points_awarded` award no points. The day board reads these awarded points via `COALESCE(a.points_awarded, t.points)`.

## Break periods

A user on a `tasks` break period ([`modules/breaks`](../breaks/README.md)) is excluded from the daily rotation:

- `get_daily_assignments(day)` first calls `fail_stale_pending_assignments(day)` and `fail_break_period_pending_assignments(day)`, then filters the active users that are on break before running the assignment algorithm. If every active user is on break, it returns `[]`.
- `mark_assignment_done` returns `ON_BREAK_PERIOD` when the user is on break (the task is still resolved, so the caller can name it).
- `toggle_assignment` returns `None` when trying to complete a task while on break. Un-completing an already completed assignment is still allowed.
- `get_day_board` hides the assignments of users on break and skips `failed` rows.

## Errors

| Error | Description |
|---|---|
| `TaskAlreadyExistsError` | Raised by repository when creating or updating a task with a duplicate active name |

## Dependencies

- `core/` for DB connection, date utilities, and string utilities
- `modules/breaks/` to exclude users on a `tasks` break period from the rotation
- Does NOT import from `apps/`