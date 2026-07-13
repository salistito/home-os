from datetime import datetime, timedelta

from core.utils.date import get_now
from modules.reminders import repository
from modules.reminders.errors import ReminderAlreadyExistsError
from modules.reminders.types import (
    Reminder,
    ReminderOperationResult,
    ReminderOperationStatus,
    ReminderRecurrence,
)


def _calculate_next_trigger_at(trigger_at: str, recurrence: str) -> str | None:
    if recurrence == "none":
        return None

    base = datetime.strptime(trigger_at, "%Y-%m-%d")

    if recurrence == "daily":
        next_date = base + timedelta(days=1)
    elif recurrence == "weekly":
        next_date = base + timedelta(weeks=1)
    elif recurrence == "monthly":
        month = base.month + 1
        year = base.year
        if month > 12:
            month = 1
            year += 1
        next_date = base.replace(year=year, month=month)
    elif recurrence == "yearly":
        next_date = base.replace(year=base.year + 1)
    else:
        return None

    return next_date.isoformat()


def create_reminder(
    user_id: str,
    message: str,
    trigger_at: str,
    trigger_time: str | None,
    recurrence: str,
) -> ReminderOperationResult:
    message = message.strip()
    if not message:
        return ReminderOperationResult(None, ReminderOperationStatus.INVALID)

    try:
        recurrence_enum = ReminderRecurrence(recurrence)
    except ValueError:
        return ReminderOperationResult(None, ReminderOperationStatus.INVALID)

    now = get_now()
    now_date = now.date().isoformat()
    now_time = now.strftime("%H:%M")

    if trigger_at < now_date:
        return ReminderOperationResult(None, ReminderOperationStatus.PAST_TIME)
    if trigger_at == now_date and trigger_time and trigger_time <= now_time:
        return ReminderOperationResult(None, ReminderOperationStatus.PAST_TIME)

    try:
        reminder = repository.create_reminder(
            user_id, message, trigger_at, trigger_time, recurrence_enum
        )
    except ReminderAlreadyExistsError as e:
        return ReminderOperationResult(e.reminder, ReminderOperationStatus.DUPLICATE_MESSAGE)
    return ReminderOperationResult(reminder, ReminderOperationStatus.OK)


def get_user_reminders(user_id: str) -> list[Reminder]:
    return repository.get_user_reminders(user_id)


def get_user_pending_reminders(user_id: str) -> list[Reminder]:
    now = get_now()
    now_date = now.date().isoformat()
    return repository.get_user_pending_reminders(user_id, now_date)


def get_due_day_reminders() -> list[Reminder]:
    now = get_now()
    now_date = now.date().isoformat()
    return repository.get_due_day_reminders(now_date)


def get_due_timed_reminders() -> list[Reminder]:
    now = get_now()
    now_date = now.date().isoformat()
    now_time = now.strftime("%H:%M")
    return repository.get_due_timed_reminders(now_date, now_time)


def advance_recurrence(reminder: Reminder) -> Reminder | None:
    next_trigger_at = _calculate_next_trigger_at(reminder.trigger_at, reminder.recurrence.value)
    if next_trigger_at is None:
        return None

    repository.update_reminder(reminder.id, reminder.user_id, trigger_at=next_trigger_at)
    return repository.get_reminder_by_id(reminder.id)


def update_reminder(
    reminder_id: int, user_id: str, **kwargs: str | None
) -> ReminderOperationResult:
    reminder = repository.get_reminder_by_id(reminder_id)
    if reminder is None:
        return ReminderOperationResult(None, ReminderOperationStatus.NOT_FOUND)

    if reminder.user_id != user_id:
        return ReminderOperationResult(None, ReminderOperationStatus.NOT_FOUND)

    fields = {
        k: v
        for k, v in kwargs.items()
        if k in repository.EDITABLE_REMINDER_COLUMNS and v is not None
    }
    if not fields:
        return ReminderOperationResult(None, ReminderOperationStatus.INVALID)

    if "message" in fields:
        fields["message"] = fields["message"].strip()
        if not fields["message"]:
            return ReminderOperationResult(None, ReminderOperationStatus.INVALID)

    if "recurrence" in fields:
        try:
            ReminderRecurrence(fields["recurrence"])
        except ValueError:
            return ReminderOperationResult(None, ReminderOperationStatus.INVALID)

    repository.update_reminder(reminder_id, user_id, **fields)
    updated = repository.get_reminder_by_id(reminder_id)
    return ReminderOperationResult(updated, ReminderOperationStatus.OK)


def delete_reminder(reminder_id: int, user_id: str) -> ReminderOperationResult:
    reminder = repository.get_reminder_by_id(reminder_id)
    if reminder is None:
        return ReminderOperationResult(None, ReminderOperationStatus.NOT_FOUND)

    success = repository.delete_reminder(reminder_id, user_id)
    if not success:
        return ReminderOperationResult(None, ReminderOperationStatus.NOT_FOUND)

    return ReminderOperationResult(reminder, ReminderOperationStatus.OK)


def delete_reminder_by_message(user_id: str, message: str) -> ReminderOperationResult:
    reminder = repository.get_reminder_by_message(user_id, message)
    if reminder is None:
        return ReminderOperationResult(None, ReminderOperationStatus.NOT_FOUND)

    success = repository.delete_reminder(reminder.id, user_id)
    if not success:
        return ReminderOperationResult(None, ReminderOperationStatus.NOT_FOUND)

    return ReminderOperationResult(reminder, ReminderOperationStatus.OK)
