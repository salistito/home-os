# reminders

Domain module for reminder management.

## Public API

```python
def is_valid_recurrence(value: str) -> bool

def calculate_next_trigger_at(trigger_at: str, recurrence: str, trigger_time: str | None = None) -> str | None

def calculate_next_trigger_time(trigger_at: str, trigger_time: str | None, recurrence: str) -> str | None

def is_past(trigger_at: str, trigger_time: str | None) -> bool

def create_reminder(user_id: int, message: str, trigger_at: str, trigger_time: str | None, recurrence: str) -> ReminderOperationResult

def get_user_reminders(user_id: int) -> list[Reminder]

def get_user_pending_reminders(user_id: int) -> list[Reminder]

def get_due_day_reminders() -> list[Reminder]

def get_due_timed_reminders() -> list[Reminder]

def advance_recurrence(reminder: Reminder) -> Reminder | None

def update_reminder(reminder_id: int, user_id: int, **kwargs: str | None) -> ReminderOperationResult

def delete_reminder(reminder_id: int, user_id: int) -> ReminderOperationResult

def delete_reminder_by_message(user_id: int, message: str) -> ReminderOperationResult

def process_reminder_states(reminders: list[Reminder]) -> None

def create_system_reminder(system_ref_entity: str, system_ref_entity_id: str, user_id: int, message: str, trigger_at: str, trigger_time: str | None = None, recurrence: str = "none") -> ReminderOperationResult

def delete_system_reminders_by_entity(user_id: int, system_ref_entity: str, system_ref_entity_id: str) -> None
```

## Key types

| Type | Description |
|---|---|
| `Reminder` | A reminder with `user_id`, `message`, `trigger_at`/`trigger_time`, `recurrence`, optional `cron_job_id`, `owner` (`user` or `system`), and optional `system_ref_entity`/`system_ref_entity_id` |
| `ReminderOperationResult` | Result of create/update/delete with `Reminder | None` and `ReminderOperationStatus` |
| `ReminderOperationStatus` | Enum: `OK`, `INVALID`, `PAST_TIME`, `DUPLICATE_MESSAGE`, `NOT_FOUND` |
| `ReminderRecurrence` | Enum with the presets: `NONE`, `DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY` |
| `ReminderOwner` | Enum: `USER`, `SYSTEM` |

`recurrence` is stored as a plain string. It accepts the presets above or a custom
interval like `12h`, `9d`, `6w`, `3m`, `2y` (`h`ours, `d`ays, `w`eeks, `m`onths, `y`ears). Hour intervals require a `trigger_time`. Use `is_valid_recurrence()` from
`modules.reminders.service` to validate.

## Errors

| Error | Description |
|---|---|
| `ReminderAlreadyExistsError` | Raised by repository when creating a reminder with a duplicate message, or updating a reminder's message to one that already exists (no service pre-check on the update path) |

## External integrations

- `cron.py` integrates with the [cron-job.org REST API](https://docs.cron-job.org/rest-api.html) via `httpx` to create, update, and delete one-shot cron jobs for timed reminders. Requires `CRONJOB_ORG_API_KEY`, `WEBHOOK_URL`, and `WEBHOOK_SECRET` env vars.

## Dependencies

- `core/` for DB connection, config, date utilities, and string utilities
- `httpx` for cron-job.org API calls
- Does NOT import from `apps/`
