# reminders

Domain module for reminder management.

## Public API

```python
def create_reminder(user_id: str, message: str, trigger_at: str, trigger_time: str | None, recurrence: str) -> ReminderOperationResult

def get_user_reminders(user_id: str) -> list[Reminder]

def get_user_pending_reminders(user_id: str) -> list[Reminder]

def get_due_day_reminders() -> list[Reminder]

def get_due_timed_reminders() -> list[Reminder]

def advance_recurrence(reminder: Reminder) -> Reminder | None

def update_reminder(reminder_id: int, user_id: str, **kwargs: str | None) -> ReminderOperationResult

def delete_reminder(reminder_id: int, user_id: str) -> ReminderOperationResult

def delete_reminder_by_message(user_id: str, message: str) -> ReminderOperationResult
```

## Key types

| Type | Description |
|---|---|
| `Reminder` | A user reminder with message, trigger date/time, and recurrence |
| `ReminderOperationResult` | Result of create/update/delete with `Reminder | None` and `ReminderOperationStatus` |
| `ReminderOperationStatus` | Enum: `OK`, `INVALID`, `PAST_TIME`, `DUPLICATE_MESSAGE`, `NOT_FOUND` |
| `ReminderRecurrence` | Enum: `NONE`, `DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY` |

## Errors

| Error | Description |
|---|---|
| `ReminderAlreadyExistsError` | Raised by repository when creating a reminder with a duplicate message |
| `ReminderNotFoundError` | Raised when a reminder is not found by id |

## Dependencies

- `core/` for DB connection, date utilities, and string utilities
- Does NOT import from `apps/`
