import calendar
import re
from datetime import datetime, timedelta

from core.utils.date import get_now
from modules.reminders import cron, repository
from modules.reminders.errors import ReminderAlreadyExistsError
from modules.reminders.types import (
    Reminder,
    ReminderOperationResult,
    ReminderOperationStatus,
    ReminderOwner,
    ReminderRecurrence,
)

RECURRENCE_PRESETS = frozenset(recurrence.value for recurrence in ReminderRecurrence)

CUSTOM_RECURRENCE_REGEX = re.compile(r"^([1-9]\d*)([hdwmy])$")


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


def is_valid_recurrence(value: str) -> bool:
    if value in RECURRENCE_PRESETS:
        return True
    return CUSTOM_RECURRENCE_REGEX.match(value) is not None


def _parse_custom_recurrence(recurrence: str) -> tuple[int, str] | None:
    match = CUSTOM_RECURRENCE_REGEX.match(recurrence)
    if match is None:
        return None
    amount, unit = int(match.group(1)), match.group(2)
    return amount, unit


def _custom_unit(recurrence: str) -> str | None:
    parsed_recurrence = _parse_custom_recurrence(recurrence)
    return parsed_recurrence[1] if parsed_recurrence else None


def _add_months(base: datetime, months: int) -> datetime:
    total = base.month - 1 + months
    year = base.year + total // 12
    month = total % 12 + 1
    day = min(base.day, calendar.monthrange(year, month)[1])
    return base.replace(year=year, month=month, day=day)


def calculate_next_trigger_at(
    trigger_at: str, recurrence: str, trigger_time: str | None = None
) -> str | None:
    if recurrence == "none":
        return None

    base = datetime.strptime(trigger_at, "%Y-%m-%d")

    if recurrence == "daily":
        next_date = base + timedelta(days=1)
    elif recurrence == "weekly":
        next_date = base + timedelta(weeks=1)
    elif recurrence == "monthly":
        next_date = _add_months(base, 1)
    elif recurrence == "yearly":
        next_date = _add_months(base, 12)
    else:
        parsed_recurrence = _parse_custom_recurrence(recurrence)
        if parsed_recurrence is None:
            return None
        amount, unit = parsed_recurrence
        if unit == "h":
            if trigger_time is None:
                return None
            dt = datetime.strptime(f"{trigger_at} {trigger_time}", "%Y-%m-%d %H:%M")
            next_date = dt + timedelta(hours=amount)
        elif unit == "d":
            next_date = base + timedelta(days=amount)
        elif unit == "w":
            next_date = base + timedelta(weeks=amount)
        elif unit == "m":
            next_date = _add_months(base, amount)
        elif unit == "y":
            next_date = _add_months(base, amount * 12)
        else:
            return None

    return next_date.date().isoformat()


def calculate_next_trigger_time(
    trigger_at: str, trigger_time: str | None, recurrence: str
) -> str | None:
    parsed_recurrence = _parse_custom_recurrence(recurrence)
    if parsed_recurrence is None or parsed_recurrence[1] != "h" or trigger_time is None:
        return None
    dt = datetime.strptime(f"{trigger_at} {trigger_time}", "%Y-%m-%d %H:%M")
    return (dt + timedelta(hours=parsed_recurrence[0])).strftime("%H:%M")


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
        return ReminderOperationResult(status=ReminderOperationStatus.INVALID)

    if not is_valid_recurrence(recurrence):
        return ReminderOperationResult(status=ReminderOperationStatus.INVALID)

    if not _is_valid_date(trigger_at):
        return ReminderOperationResult(status=ReminderOperationStatus.INVALID)
    if trigger_time is not None and not _is_valid_time(trigger_time):
        return ReminderOperationResult(status=ReminderOperationStatus.INVALID)
    if trigger_time is None and _custom_unit(recurrence) == "h":
        return ReminderOperationResult(status=ReminderOperationStatus.INVALID)
    if is_past(trigger_at, trigger_time):
        return ReminderOperationResult(status=ReminderOperationStatus.PAST_TIME)

    cron_job_id = None
    need_create_cron_job = trigger_time is not None
    if need_create_cron_job:
        cron_job_id = cron.create_one_shot_job(trigger_at, trigger_time)

    try:
        reminder = repository.create_reminder(
            user_id, message, trigger_at, trigger_time, recurrence, cron_job_id
        )
    except ReminderAlreadyExistsError as e:
        if cron_job_id:
            cron.delete_job(cron_job_id)
        return ReminderOperationResult(
            reminder=e.reminder, status=ReminderOperationStatus.DUPLICATE_MESSAGE
        )
    return ReminderOperationResult(reminder=reminder, status=ReminderOperationStatus.OK)


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
    next_trigger_at = calculate_next_trigger_at(
        reminder.trigger_at, reminder.recurrence, reminder.trigger_time
    )
    if next_trigger_at is None:
        return None

    next_trigger_time = calculate_next_trigger_time(
        reminder.trigger_at, reminder.trigger_time, reminder.recurrence
    )
    if next_trigger_time is not None:
        repository.update_reminder_schedule(reminder.id, next_trigger_at, next_trigger_time)
    else:
        repository.update_reminder_trigger_at(reminder.id, trigger_at=next_trigger_at)

    need_create_cron_job = reminder.trigger_time and not reminder.cron_job_id
    need_update_cron_job = reminder.trigger_time and reminder.cron_job_id
    if need_update_cron_job:
        cron.update_job(
            reminder.cron_job_id, next_trigger_at, next_trigger_time or reminder.trigger_time
        )
    elif need_create_cron_job:
        job_id = cron.create_one_shot_job(
            next_trigger_at, next_trigger_time or reminder.trigger_time
        )
        repository.update_reminder_cron_job_id(reminder.id, job_id)

    return repository.get_reminder_by_id(reminder.id)


def update_reminder(
    reminder_id: int, user_id: int, **kwargs: str | None
) -> ReminderOperationResult:
    reminder = repository.get_reminder_by_id(reminder_id)
    if reminder is None:
        return ReminderOperationResult(status=ReminderOperationStatus.NOT_FOUND)

    if reminder.user_id != user_id:
        return ReminderOperationResult(status=ReminderOperationStatus.NOT_FOUND)

    fields = {
        k: v
        for k, v in kwargs.items()
        if k in repository.EDITABLE_REMINDER_COLUMNS and (v is not None or k == "trigger_time")
    }
    if not fields:
        return ReminderOperationResult(status=ReminderOperationStatus.INVALID)

    if "message" in fields:
        fields["message"] = fields["message"].strip()
        if not fields["message"]:
            return ReminderOperationResult(status=ReminderOperationStatus.INVALID)

    if "trigger_at" in fields and not _is_valid_date(fields["trigger_at"]):
        return ReminderOperationResult(status=ReminderOperationStatus.INVALID)

    if "trigger_time" in fields and fields["trigger_time"] is not None:
        if not _is_valid_time(fields["trigger_time"]):
            return ReminderOperationResult(status=ReminderOperationStatus.INVALID)

    trigger_at = fields.get("trigger_at", reminder.trigger_at)
    trigger_time = fields.get("trigger_time", reminder.trigger_time)
    if is_past(trigger_at, trigger_time):
        return ReminderOperationResult(status=ReminderOperationStatus.PAST_TIME)

    if "recurrence" in fields:
        if not is_valid_recurrence(fields["recurrence"]):
            return ReminderOperationResult(status=ReminderOperationStatus.INVALID)

    recurrence = fields.get("recurrence", reminder.recurrence)
    if trigger_time is None and _custom_unit(recurrence) == "h":
        return ReminderOperationResult(status=ReminderOperationStatus.INVALID)

    repository.update_reminder(reminder_id, user_id, **fields)
    updated = repository.get_reminder_by_id(reminder_id)

    time_changed = "trigger_at" in fields or "trigger_time" in fields
    if time_changed:
        if updated.trigger_time:
            if updated.cron_job_id:
                # time_changed, reminder has trigger_time and associated
                # cron_job_id, update cron job schedule.
                cron.update_job(updated.cron_job_id, updated.trigger_at, updated.trigger_time)
            else:
                # time_changed, reminder has trigger_time but no cron_job_id, create one.
                job_id = cron.create_one_shot_job(updated.trigger_at, updated.trigger_time)
                repository.update_reminder_cron_job_id(reminder_id, job_id)
                updated = repository.get_reminder_by_id(reminder_id)
        elif updated.cron_job_id:
            # time_changed, reminder has no trigger_time but still has
            # an associated cron_job_id, delete it.
            cron.delete_job(updated.cron_job_id)
            repository.update_reminder_cron_job_id(reminder_id, None)
            updated = repository.get_reminder_by_id(reminder_id)

    return ReminderOperationResult(reminder=updated, status=ReminderOperationStatus.OK)


def delete_reminder(reminder_id: int, user_id: int) -> ReminderOperationResult:
    reminder = repository.get_reminder_by_id(reminder_id)
    if reminder is None:
        return ReminderOperationResult(status=ReminderOperationStatus.NOT_FOUND)

    if reminder.cron_job_id:
        cron.delete_job(reminder.cron_job_id)

    success = repository.delete_reminder(reminder_id, user_id)
    if not success:
        return ReminderOperationResult(status=ReminderOperationStatus.NOT_FOUND)

    return ReminderOperationResult(reminder=reminder, status=ReminderOperationStatus.OK)


def delete_reminder_by_message(user_id: int, message: str) -> ReminderOperationResult:
    reminder = repository.get_reminder_by_message(user_id, message)
    if reminder is None:
        return ReminderOperationResult(status=ReminderOperationStatus.NOT_FOUND)

    if reminder.cron_job_id:
        cron.delete_job(reminder.cron_job_id)

    success = repository.delete_reminder(reminder.id, user_id)
    if not success:
        return ReminderOperationResult(status=ReminderOperationStatus.NOT_FOUND)

    return ReminderOperationResult(reminder=reminder, status=ReminderOperationStatus.OK)


def process_reminder_states(reminders: list[Reminder]) -> None:
    for reminder in reminders:
        if reminder.recurrence == "none":
            if reminder.owner == ReminderOwner.USER:
                delete_reminder(reminder.id, reminder.user_id)
            else:
                repository.delete_system_reminder(reminder.id)
        else:
            advance_recurrence(reminder)


def create_system_reminder(
    system_ref_entity: str,
    system_ref_entity_id: str,
    user_id: int,
    message: str,
    trigger_at: str,
    trigger_time: str | None = None,
    recurrence: str = "none",
) -> ReminderOperationResult:
    message = message.strip()
    if not message:
        return ReminderOperationResult(status=ReminderOperationStatus.INVALID)

    if not _is_valid_date(trigger_at):
        return ReminderOperationResult(status=ReminderOperationStatus.INVALID)

    if trigger_time is not None and not _is_valid_time(trigger_time):
        return ReminderOperationResult(status=ReminderOperationStatus.INVALID)

    if is_past(trigger_at, trigger_time):
        return ReminderOperationResult(status=ReminderOperationStatus.PAST_TIME)

    if not is_valid_recurrence(recurrence):
        return ReminderOperationResult(status=ReminderOperationStatus.INVALID)

    if trigger_time is None and _custom_unit(recurrence) == "h":
        return ReminderOperationResult(status=ReminderOperationStatus.INVALID)

    if not system_ref_entity or not system_ref_entity.strip():
        return ReminderOperationResult(status=ReminderOperationStatus.INVALID)
    if not system_ref_entity_id or not str(system_ref_entity_id).strip():
        return ReminderOperationResult(status=ReminderOperationStatus.INVALID)

    cron_job_id = None
    if trigger_time is not None:
        cron_job_id = cron.create_one_shot_job(trigger_at, trigger_time)

    try:
        reminder = repository.upsert_system_reminder(
            system_ref_entity=system_ref_entity,
            system_ref_entity_id=str(system_ref_entity_id),
            user_id=user_id,
            message=message,
            trigger_at=trigger_at,
            trigger_time=trigger_time,
            recurrence=recurrence,
            cron_job_id=cron_job_id,
        )
    except Exception:
        if cron_job_id:
            cron.delete_job(cron_job_id)
        raise

    return ReminderOperationResult(reminder=reminder, status=ReminderOperationStatus.OK)


def delete_system_reminders_by_entity(
    user_id: int, system_ref_entity: str, system_ref_entity_id: str
) -> None:
    repository.delete_system_reminders_by_entity(user_id, system_ref_entity, system_ref_entity_id)
