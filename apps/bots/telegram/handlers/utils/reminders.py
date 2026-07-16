import re

from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from apps.bots.telegram.messages_es import (
    add_reminder_ask_recurrence,
    add_reminder_ask_time,
    add_reminder_usage,
    create_reminder_error,
    delete_reminder_usage,
    edit_reminder_ask_field,
    edit_reminder_ask_value,
    edit_reminder_usage,
    reminder_created,
    reminder_deleted,
    reminder_duplicate_message,
    reminder_invalid,
    reminder_invalid_recurrence,
    reminder_invalid_time,
    reminder_not_found_by_message,
    reminder_past_time,
    reminder_updated,
)
from core.utils.date import get_now, to_db_date
from core.utils.string import html_escape
from modules.reminders.repository import get_reminder_by_message
from modules.reminders.service import create_reminder, update_reminder, delete_reminder_by_message
from modules.reminders.types import ReminderOperationStatus, ReminderRecurrence


EDITABLE_REMINDER_PROPS = {
    "message": "message",
    "trigger_at": "trigger_at",
    "trigger_time": "trigger_time",
    "recurrence": "recurrence",
}


def parse_relative_time(text: str) -> tuple[str, str | None] | None:
    text = text.strip()
    match = re.match(r"^(\d+)(h|m|d|w)(\d+)?(h|m|d|w)?$", text)
    if not match:
        return None

    now = get_now()
    total = timedelta()
    i = 1
    while i <= 4 and match.group(i):
        value = int(match.group(i))
        unit = match.group(i + 1)
        if unit == "h":
            total += timedelta(hours=value)
        elif unit == "m":
            total += timedelta(minutes=value)
        elif unit == "d":
            total += timedelta(days=value)
        elif unit == "w":
            total += timedelta(weeks=value)
        i += 2

    result = now + total
    return to_db_date(result.date()), result.strftime("%H:%M")


def parse_absolute_date(text: str) -> tuple[str, str | None] | None:
    parts = text.strip().split()
    if len(parts) == 1:
        try:
            datetime.strptime(parts[0], "%Y-%m-%d")
            return parts[0], None
        except ValueError:
            return None
    elif len(parts) == 2:
        try:
            datetime.strptime(parts[0], "%Y-%m-%d")
            datetime.strptime(parts[1], "%H:%M")
            return parts[0], parts[1]
        except ValueError:
            return None
    return None


def parse_add_reminder_args(text: str) -> tuple[str, str | None, str, str] | None:
    # add_reminder <message> <relative_time | date> [time] <recurrence>
    text = text.removeprefix("/add_reminder").strip()
    if not text:
        return None

    words = text.split()
    if len(words) < 2:
        return None

    recurrence = "none"
    if coerce_recurrence(words[-1]):
        recurrence = words[-1]
        words = words[:-1]

    if len(words) < 2:
        return None

    if len(words) >= 3:
        try:
            datetime.strptime(words[-2], "%Y-%m-%d")
            datetime.strptime(words[-1], "%H:%M")
            reminder_message, trigger_at, trigger_time = " ".join(words[:-2]), words[-2], words[-1]
            return reminder_message, trigger_at, trigger_time, recurrence
        except ValueError:
            pass

    parsed = parse_relative_time(words[-1])
    if parsed:
        reminder_message, trigger_at, trigger_time = " ".join(words[:-1]), parsed[0], parsed[1]
        return reminder_message, trigger_at, trigger_time, recurrence

    try:
        datetime.strptime(words[-1], "%Y-%m-%d")
        reminder_message, trigger_at = " ".join(words[:-1]), words[-1]
        return reminder_message, trigger_at, None, recurrence
    except ValueError:
        return None


def parse_edit_reminder_args(text: str) -> tuple[str, str, str] | None:
    args = text.split()  # edit_reminder <message> <field> <value>
    if len(args) < 4:
        return None

    for i in range(1, len(args) - 1):
        if args[i] in EDITABLE_REMINDER_PROPS:
            reminder_message = " ".join(args[1:i])
            field = args[i]
            value = " ".join(args[i + 1 :])
            if not reminder_message or not value:
                return None
            return html_escape(reminder_message), field, html_escape(value)

    return None


def parse_delete_reminder_args(text: str) -> str | None:
    args = text.split()  # /delete_reminder <message>
    if len(args) < 2:
        return None
    reminder_message = " ".join(args[1:])
    return html_escape(reminder_message)


def coerce_recurrence(value: str) -> ReminderRecurrence | None:
    try:
        return ReminderRecurrence(value)
    except ValueError:
        return None


def _common_reminder_errors(result) -> str | None:
    match result.status:
        case ReminderOperationStatus.INVALID:
            return reminder_invalid()
        case ReminderOperationStatus.PAST_TIME:
            return reminder_past_time()
        case ReminderOperationStatus.DUPLICATE_MESSAGE:
            return reminder_duplicate_message(result.reminder.message)
    return None


def add_reminder_reply(result) -> str:
    if msg := _common_reminder_errors(result):
        return msg
    if result.status is ReminderOperationStatus.OK:
        return reminder_created(result.reminder)
    return add_reminder_usage()


def update_reminder_reply(
    result, reminder_message: str, field: str, old_value: str, new_value: str
) -> str:
    if msg := _common_reminder_errors(result):
        return msg
    match result.status:
        case ReminderOperationStatus.OK:
            return reminder_updated(reminder_message, field, old_value, new_value)
        case ReminderOperationStatus.NOT_FOUND:
            return reminder_not_found_by_message(reminder_message)
    return edit_reminder_usage()


def delete_reminder_reply(result, reminder_message: str) -> str:
    match result.status:
        case ReminderOperationStatus.OK:
            return reminder_deleted(reminder_message)
        case ReminderOperationStatus.NOT_FOUND:
            return reminder_not_found_by_message(reminder_message)
    return delete_reminder_usage()


async def handle_add_reminder_wizard(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user
) -> bool:
    add_reminder_step = context.user_data.get("add_reminder_step")
    if not add_reminder_step:
        return False

    text = html_escape(update.message.text)

    if add_reminder_step == "message":
        context.user_data["reminder_message"] = text
        context.user_data["add_reminder_step"] = "time"
        await update.message.reply_text(add_reminder_ask_time())
        return True

    if add_reminder_step == "time":
        parsed = parse_relative_time(text)
        if not parsed:
            parsed = parse_absolute_date(text)
        if not parsed:
            await update.message.reply_text(reminder_invalid_time())
            return True

        context.user_data["reminder_trigger_at"] = parsed[0]
        context.user_data["reminder_trigger_time"] = parsed[1]
        context.user_data["add_reminder_step"] = "recurrence"
        await update.message.reply_text(add_reminder_ask_recurrence())
        return True

    if add_reminder_step == "recurrence":
        context.user_data.pop("add_reminder_step", None)
        reminder_message = context.user_data.pop("reminder_message", None)
        reminder_trigger_at = context.user_data.pop("reminder_trigger_at", None)
        reminder_trigger_time = context.user_data.pop("reminder_trigger_time", None)

        recurrence = coerce_recurrence(text)
        if recurrence is None:
            await update.message.reply_text(reminder_invalid_recurrence())
            return True

        result = create_reminder(
            user.id, reminder_message, reminder_trigger_at, reminder_trigger_time, text
        )
        match result.status:
            case ReminderOperationStatus.OK:
                await update.message.reply_text(reminder_created(result.reminder))
            case _:
                await update.message.reply_text(create_reminder_error())
        return True

    return False


async def handle_edit_reminder_wizard(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user
) -> bool:
    edit_reminder_step = context.user_data.get("edit_reminder_step")
    if not edit_reminder_step:
        return False

    text = html_escape(update.message.text)

    if edit_reminder_step == "message":
        reminder = get_reminder_by_message(user.id, text)
        if reminder is None:
            context.user_data.pop("edit_reminder_step", None)
            await update.message.reply_text(reminder_not_found_by_message(text))
            return True
        context.user_data["edit_reminder_message"] = text
        context.user_data["edit_reminder_step"] = "field"
        await update.message.reply_text(edit_reminder_ask_field())
        return True

    if edit_reminder_step == "field":
        if text not in EDITABLE_REMINDER_PROPS:
            await update.message.reply_text(edit_reminder_ask_field())
            return True
        context.user_data["edit_reminder_field"] = text
        context.user_data["edit_reminder_step"] = "value"
        await update.message.reply_text(edit_reminder_ask_value())
        return True

    if edit_reminder_step == "value":
        context.user_data.pop("edit_reminder_step", None)
        reminder_message = context.user_data.pop("edit_reminder_message", None)
        field = context.user_data.pop("edit_reminder_field", None)
        db_field = EDITABLE_REMINDER_PROPS[field]

        if field == "recurrence":
            if coerce_recurrence(text) is None:
                await update.message.reply_text(reminder_invalid_recurrence())
                return True

        reminder = get_reminder_by_message(user.id, reminder_message)
        if reminder is None:
            await update.message.reply_text(reminder_not_found_by_message(reminder_message))
            return True

        old_value = str(getattr(reminder, field)) if getattr(reminder, field) is not None else "-"
        result = update_reminder(reminder.id, user.id, **{db_field: text})
        await update.message.reply_text(
            update_reminder_reply(result, reminder_message, field, old_value, text)
        )
        return True

    return False


async def handle_delete_reminder_wizard(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user
) -> bool:
    delete_reminder_step = context.user_data.get("delete_reminder_step")
    if not delete_reminder_step:
        return False

    text = html_escape(update.message.text)
    context.user_data.pop("delete_reminder_step", None)

    reminder = get_reminder_by_message(user.id, text)
    if reminder is None:
        await update.message.reply_text(reminder_not_found_by_message(text))
        return True

    result = delete_reminder_by_message(user.id, text)
    await update.message.reply_text(delete_reminder_reply(result, text))
    return True
