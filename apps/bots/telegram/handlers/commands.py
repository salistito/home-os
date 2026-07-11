from functools import wraps

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from apps.bots.telegram.handlers.messages import build_assignment_list
from apps.bots.telegram.messages_es import (
    add_task_usage,
    balance,
    delete_task_usage,
    edit_task_usage,
    list_tasks,
    no_pending_assignments,
    start_welcome,
    task_created,
    tasks_crud_explanation,
    task_deleted,
    task_duplicate_name,
    task_has_assignments_error,
    task_invalid_frequency,
    task_invalid_name,
    task_invalid_points,
    task_not_found_by_name,
    task_updated,
    user_not_registered,
)
from core.identity import get_user_by_chat_id, get_users
from core.utils.date import get_today, month_key
from core.utils.string import html_escape
from modules.tasks.repository import find_active_task_by_name, get_active_tasks
from modules.tasks.service import (
    create_task,
    fail_stale_pending_assignments,
    get_daily_assignments,
    get_month_balance,
    soft_delete_active_task,
    update_active_task,
)
from modules.tasks.types import TaskOperationStatus


def _parse_add_task_args(text: str) -> tuple[str, int, int | None] | None:
    args = text.split()  # /add_task <name> <points> [freq]
    if len(args) < 3:
        return None

    if len(args) == 3:
        try:
            points = int(args[-1])
        except ValueError:
            return None
        freq = None

    elif len(args) >= 4:
        try:
            freq = int(args[-1])
            points = int(args[-2])
        except ValueError:
            try:
                points = int(args[-1])
            except ValueError:
                return None
            freq = None

    task_name_end = -2 if freq is not None else -1
    task_name = " ".join(args[1:task_name_end])
    return html_escape(task_name), points, freq


_EDITABLE_TASK_PROPS = {"name": "name", "points": "points", "freq": "frequency_days"}


def _parse_edit_task_args(text: str) -> tuple[str, str, str] | None:
    args = text.split()  # /edit_task <name> <field> <value>
    if len(args) < 4:
        return None

    for i in range(1, len(args) - 1):
        if args[i] in _EDITABLE_TASK_PROPS:
            task_name = " ".join(args[1:i])
            field = args[i]
            value = " ".join(args[i + 1 :])
            if not task_name or not value:
                return None
            return html_escape(task_name), field, html_escape(value)

    return None


def _coerce_edit_value(db_field: str, value: str) -> object:
    if db_field == "points":
        return int(value)
    if db_field == "frequency_days":
        return None if value in ("0", "-") else int(value)
    return value


def _parse_delete_task_args(text: str) -> str | None:
    args = text.split()  # /delete_task <name>
    if len(args) < 2:
        return None
    task_name = " ".join(args[1:])
    return html_escape(task_name)


def _common_task_errors(result) -> str | None:
    match result.status:
        case TaskOperationStatus.INVALID_NAME:
            return task_invalid_name()
        case TaskOperationStatus.INVALID_POINTS:
            return task_invalid_points()
        case TaskOperationStatus.INVALID_FREQUENCY:
            return task_invalid_frequency()
        case TaskOperationStatus.DUPLICATE_NAME:
            return task_duplicate_name(result.task.name)
    return None


def _add_task_reply(result) -> str:
    if msg := _common_task_errors(result):
        return msg
    if result.status is TaskOperationStatus.OK:
        return task_created(result.task)
    return add_task_usage()


def _update_task_reply(result, task_name: str, field: str, old_value: str, new_value: str) -> str:
    if msg := _common_task_errors(result):
        return msg
    match result.status:
        case TaskOperationStatus.OK:
            return task_updated(result.task.name, field, old_value, new_value)
        case TaskOperationStatus.NOT_FOUND:
            return task_not_found_by_name(task_name)
    return edit_task_usage()


def _delete_task_reply(result, task_name: str) -> str:
    match result.status:
        case TaskOperationStatus.OK:
            return task_deleted(result.task.name)
        case TaskOperationStatus.NOT_FOUND:
            return task_not_found_by_name(task_name)
        case TaskOperationStatus.HAS_ASSIGNMENTS:
            return task_has_assignments_error(result.task.name)
    return delete_task_usage()


def require_registration(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = get_user_by_chat_id(str(update.effective_chat.id))
        if user is None:
            await update.message.reply_text(user_not_registered())
            return
        return await func(update, context, user)

    return wrapper


async def on_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(start_welcome())


async def on_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await on_start_command(update, context)


@require_registration
async def on_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> None:
    await update.message.reply_text(tasks_crud_explanation(), parse_mode=ParseMode.HTML)


@require_registration
async def on_add_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> None:
    args = _parse_add_task_args(update.message.text)
    if args is None:
        await update.message.reply_text(add_task_usage())
        return
    name, points, frequency_days = args
    next_due_date = get_today() if frequency_days is not None else None
    result = create_task(name, points, frequency_days, next_due_date)
    await update.message.reply_text(_add_task_reply(result))


@require_registration
async def on_list_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> None:
    tasks = get_active_tasks()
    text = list_tasks(tasks)
    await update.message.reply_text(text)


@require_registration
async def on_edit_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> None:
    args = _parse_edit_task_args(update.message.text)
    if args is None:
        await update.message.reply_text(edit_task_usage(), parse_mode=ParseMode.HTML)
        return
    task_name, field, value = args
    task = find_active_task_by_name(task_name)
    if task is None:
        await update.message.reply_text(task_not_found_by_name(task_name))
        return
    db_field = _EDITABLE_TASK_PROPS[field]
    if field == "name":
        old_value = task.name
        new_value = value
    elif field == "points":
        old_value = str(task.points)
        new_value = value
    else:
        old_value = str(task.frequency_days) if task.frequency_days else "Ocasional"
        new_value = value if value else "Ocasional"
    try:
        coerced = _coerce_edit_value(db_field, value)
    except ValueError:
        msg = task_invalid_points() if db_field == "points" else task_invalid_frequency()
        await update.message.reply_text(msg)
        return
    result = update_active_task(task.id, **{db_field: coerced})
    await update.message.reply_text(
        _update_task_reply(result, task_name, field, old_value, new_value),
        parse_mode=ParseMode.HTML,
    )


@require_registration
async def on_delete_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> None:
    task_name = _parse_delete_task_args(update.message.text)
    if task_name is None:
        await update.message.reply_text(delete_task_usage())
        return
    task = find_active_task_by_name(task_name)
    if task is None:
        await update.message.reply_text(
            task_not_found_by_name(task_name), parse_mode=ParseMode.HTML
        )
        return
    result = soft_delete_active_task(task.id)
    await update.message.reply_text(
        _delete_task_reply(result, task_name), parse_mode=ParseMode.HTML
    )


@require_registration
async def on_assignments_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> None:
    today = get_today()
    fail_stale_pending_assignments(today)
    if not any(a.user_id == user.id for a in get_daily_assignments(today)):
        await update.message.reply_text(no_pending_assignments())
        return
    old_message_id = context.user_data.get("assignments_message_id")
    if old_message_id:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=old_message_id
            )
        except BadRequest:
            pass
    text, reply_markup = build_assignment_list(user, today)
    sent = await update.message.reply_text(text, reply_markup=reply_markup)
    context.user_data["assignments_message_id"] = sent.message_id


async def on_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    month = month_key(get_today())
    balance_data = get_month_balance(month)
    names = {user.id: user.name for user in get_users()}
    await update.message.reply_text(balance(month, balance_data, names))
