from datetime import datetime, timedelta

from core.utils.date import get_now
from modules.reminders import cron, repository
from modules.reminders.errors import ReminderAlreadyExistsError
from modules.reminders.types import (
    Reminder,
    ReminderOperationResult,
    ReminderOperationStatus,
    ReminderRecurrence,
)


def _is_valid_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _is_valid_time(value: str) -> bool:
    try:
        datetime.strptime(value, "%H:%M")
        return True
    except ValueError:
        return False


def calculate_next_trigger_at(trigger_at: str, recurrence: str) -> str | None:
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


def is_past(trigger_at: str, trigger_time: str | None) -> bool:
    now = get_now()
    now_date = now.date().isoformat()
    now_time = now.strftime("%H:%M")
    if trigger_at < now_date:
        return True
    if trigger_at == now_date:
        if trigger_time is None:
            return True
        if trigger_time <= now_time:
            return True
    return False


def create_reminder(
    user_id: int,
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

    if not _is_valid_date(trigger_at):
        return ReminderOperationResult(None, ReminderOperationStatus.INVALID)
    if trigger_time is not None and not _is_valid_time(trigger_time):
        return ReminderOperationResult(None, ReminderOperationStatus.INVALID)
    if is_past(trigger_at, trigger_time):
        return ReminderOperationResult(None, ReminderOperationStatus.PAST_TIME)

    cron_job_id = None
    need_create_cron_job = trigger_time is not None
    if need_create_cron_job:
        cron_job_id = cron.create_one_shot_job(trigger_at, trigger_time)

    try:
        reminder = repository.create_reminder(
            user_id, message, trigger_at, trigger_time, recurrence_enum, cron_job_id
        )
    except ReminderAlreadyExistsError as e:
        if cron_job_id:
            cron.delete_job(cron_job_id)
        return ReminderOperationResult(e.reminder, ReminderOperationStatus.DUPLICATE_MESSAGE)
    return ReminderOperationResult(reminder, ReminderOperationStatus.OK)


def get_user_reminders(user_id: int) -> list[Reminder]:
    return repository.get_user_reminders(user_id)


def get_user_pending_reminders(user_id: int) -> list[Reminder]:
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
    next_trigger_at = calculate_next_trigger_at(reminder.trigger_at, reminder.recurrence.value)
    if next_trigger_at is None:
        return None

    repository.update_reminder(reminder.id, reminder.user_id, trigger_at=next_trigger_at)

    need_create_cron_job = reminder.trigger_time and not reminder.cron_job_id
    need_update_cron_job = reminder.trigger_time and reminder.cron_job_id
    if need_update_cron_job:
        cron.update_job(reminder.cron_job_id, next_trigger_at, reminder.trigger_time)
    elif need_create_cron_job:
        job_id = cron.create_one_shot_job(next_trigger_at, reminder.trigger_time)
        repository.update_reminder_cron_job_id(reminder.id, job_id)

    return repository.get_reminder_by_id(reminder.id)


def update_reminder(
    reminder_id: int, user_id: int, **kwargs: str | None
) -> ReminderOperationResult:
    reminder = repository.get_reminder_by_id(reminder_id)
    if reminder is None:
        return ReminderOperationResult(None, ReminderOperationStatus.NOT_FOUND)

    if reminder.user_id != user_id:
        return ReminderOperationResult(None, ReminderOperationStatus.NOT_FOUND)

    fields = {
        k: v
        for k, v in kwargs.items()
        if k in repository.EDITABLE_REMINDER_COLUMNS and (v is not None or k == "trigger_time")
    }
    if not fields:
        return ReminderOperationResult(None, ReminderOperationStatus.INVALID)

    if "message" in fields:
        fields["message"] = fields["message"].strip()
        if not fields["message"]:
            return ReminderOperationResult(None, ReminderOperationStatus.INVALID)

    if "trigger_at" in fields and not _is_valid_date(fields["trigger_at"]):
        return ReminderOperationResult(None, ReminderOperationStatus.INVALID)

    if "trigger_time" in fields and fields["trigger_time"] is not None:
        if not _is_valid_time(fields["trigger_time"]):
            return ReminderOperationResult(None, ReminderOperationStatus.INVALID)

    trigger_at = fields.get("trigger_at", reminder.trigger_at)
    trigger_time = fields.get("trigger_time", reminder.trigger_time)
    if is_past(trigger_at, trigger_time):
        return ReminderOperationResult(None, ReminderOperationStatus.PAST_TIME)

    if "recurrence" in fields:
        try:
            ReminderRecurrence(fields["recurrence"])
        except ValueError:
            return ReminderOperationResult(None, ReminderOperationStatus.INVALID)

    repository.update_reminder(reminder_id, user_id, **fields)
    updated = repository.get_reminder_by_id(reminder_id)

    time_changed = "trigger_at" in fields or "trigger_time" in fields
    if time_changed:
        if updated.trigger_time:
            if updated.cron_job_id:
                # time_changed, reminder has trigger_time and associated cron_job_id, update cron job schedule.
                cron.update_job(updated.cron_job_id, updated.trigger_at, updated.trigger_time)
            else:
                # time_changed, reminder has trigger_time but no cron_job_id, create one.
                job_id = cron.create_one_shot_job(updated.trigger_at, updated.trigger_time)
                repository.update_reminder_cron_job_id(reminder_id, job_id)
                updated = repository.get_reminder_by_id(reminder_id)
        elif updated.cron_job_id:
            # time_changed, reminder has no trigger_time but still has an associated cron_job_id, delete it.
            cron.delete_job(updated.cron_job_id)
            repository.update_reminder_cron_job_id(reminder_id, None)
            updated = repository.get_reminder_by_id(reminder_id)

    return ReminderOperationResult(updated, ReminderOperationStatus.OK)


def delete_reminder(reminder_id: int, user_id: int) -> ReminderOperationResult:
    reminder = repository.get_reminder_by_id(reminder_id)
    if reminder is None:
        return ReminderOperationResult(None, ReminderOperationStatus.NOT_FOUND)

    if reminder.cron_job_id:
        cron.delete_job(reminder.cron_job_id)

    success = repository.delete_reminder(reminder_id, user_id)
    if not success:
        return ReminderOperationResult(None, ReminderOperationStatus.NOT_FOUND)

    return ReminderOperationResult(reminder, ReminderOperationStatus.OK)


def delete_reminder_by_message(user_id: int, message: str) -> ReminderOperationResult:
    reminder = repository.get_reminder_by_message(user_id, message)
    if reminder is None:
        return ReminderOperationResult(None, ReminderOperationStatus.NOT_FOUND)

    if reminder.cron_job_id:
        cron.delete_job(reminder.cron_job_id)

    success = repository.delete_reminder(reminder.id, user_id)
    if not success:
        return ReminderOperationResult(None, ReminderOperationStatus.NOT_FOUND)

    return ReminderOperationResult(reminder, ReminderOperationStatus.OK)


def process_reminder_states(reminders: list[Reminder]) -> None:
    for reminder in reminders:
        if reminder.recurrence.value == "none":
            delete_reminder(reminder.id, reminder.user_id)
        else:
            advance_recurrence(reminder)
