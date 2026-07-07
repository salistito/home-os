# tasks

Domain module for household task management. Exposes three public functions (the API contract):

```python
def get_daily_assignments(day: date) -> list[Assignment]

def mark_assignment_done(text: str, user_id: str, day: date) -> AssignmentCompletionResult

def get_month_balance(month: str) -> dict[str, int]
```

## Key types

| Type | Description |
|---|---|
| `Task` | A household chore with points, optional frequency, and next due date |
| `Assignment` | A task assigned to a user for a given day (`user_id`, `task_name`, `points`) |
| `AssignmentCompletionResult` | Result of marking an assignment done with status + points |
| `AssignmentCompletionStatus` | Enum: `OK`, `ALREADY_DONE`, `NOT_FOUND` |

## Dependencies

- `core/` for DB connection and user identity lookups
- Does NOT import from `apps/`