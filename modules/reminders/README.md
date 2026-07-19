# reminders

Domain module for reminder management.

## Public API

```python
def create_reminder(user_id: int, message: str, trigger_at: str, trigger_time: str | None, recurrence: str) -> ReminderOperationResult

def get_user_reminders(user_id: int) -> list[Reminder]

def get_user_pending_reminders(user_id: int) -> list[Reminder]

def get_due_day_reminders() -> list[Reminder]

def get_due_timed_reminders() -> list[Reminder]

def advance_recurrence(reminder: Reminder) -> Reminder | None

def update_reminder(reminder_id: int, user_id: int, **kwargs: str | None) -> ReminderOperationResult

def delete_reminder(reminder_id: int, user_id: int) -> ReminderOperationResult

def delete_reminder_by_message(user_id: int, message: str) -> ReminderOperationResult
```

## Key types

| Type | Description |
|---|---|
| `Reminder` | A user reminder with `user_id`, `message`, `trigger at/time`, `recurrence`, and optional `cron_job_id` |
| `ReminderOperationResult` | Result of create/update/delete with `Reminder | None` and `ReminderOperationStatus` |
| `ReminderOperationStatus` | Enum: `OK`, `INVALID`, `PAST_TIME`, `DUPLICATE_MESSAGE`, `NOT_FOUND` |
| `ReminderRecurrence` | Enum: `NONE`, `DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY` |

## Errors

| Error | Description |
|---|---|
| `ReminderAlreadyExistsError` | Raised by repository when creating a reminder with a duplicate message |
| `ReminderNotFoundError` | Raised when a reminder is not found by id |

## External integrations

- `cron.py` integrates with the [cron-job.org REST API](https://docs.cron-job.org/rest-api.html) via `httpx` to create, update, and delete one-shot cron jobs for timed reminders. Requires `CRONJOB_ORG_API_KEY`, `WEBHOOK_URL`, and `WEBHOOK_SECRET` env vars.

## Dependencies

- `core/` for DB connection, config, date utilities, and string utilities
- `httpx` for cron-job.org API calls
- Does NOT import from `apps/`
