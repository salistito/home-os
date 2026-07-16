from functools import wraps

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from apps.bots.telegram.handlers.messages import build_assignment_list
from apps.bots.telegram.handlers.utils.reminders import (
    EDITABLE_REMINDER_PROPS,
    parse_add_reminder_args,
    parse_edit_reminder_args,
    parse_delete_reminder_args,
    coerce_recurrence,
    add_reminder_reply,
    delete_reminder_reply,
    update_reminder_reply,
)
from apps.bots.telegram.handlers.utils.tasks import (
    EDITABLE_TASK_PROPS,
    parse_add_task_args,
    parse_edit_task_args,
    parse_delete_task_args,
    coerce_edit_value,
    add_task_reply,
    update_task_reply,
    delete_task_reply,
)
from apps.bots.telegram.messages_es import (
    add_reminder_ask_message,
    add_reminder_usage,
    add_task_usage,
    balance,
    delete_reminder_ask_message,
    delete_reminder_usage,
    delete_task_usage,
    edit_reminder_ask_message,
    edit_reminder_usage,
    edit_task_usage,
    list_reminders,
    list_tasks,
    no_pending_assignments,
    reminder_invalid_recurrence,
    reminder_not_found_by_message,
    reminders_crud_explanation,
    start_welcome,
    task_invalid_frequency,
    task_invalid_points,
    task_not_found_by_name,
    tasks_crud_explanation,
    user_not_registered,
)
from core.identity import get_user_by_chat_id, get_users
from core.utils.date import get_today, month_key, to_db_date
from modules.reminders.service import (
    create_reminder,
    delete_reminder_by_message,
    get_user_reminders,
    update_reminder,
)
from modules.reminders.repository import get_reminder_by_message
from modules.tasks.repository import get_active_task_by_name, get_active_tasks
from modules.tasks.service import (
    create_task,
    fail_stale_pending_assignments,
    get_daily_assignments,
    get_month_balance,
    soft_delete_active_task,
    update_active_task,
)


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
    args = parse_add_task_args(update.message.text)
    if args is None:
        await update.message.reply_text(add_task_usage())
        return
    task_name, points, frequency_days = args
    next_due_date = to_db_date(get_today()) if frequency_days is not None else None
    result = create_task(task_name, points, frequency_days, next_due_date)
    await update.message.reply_text(add_task_reply(result))


@require_registration
async def on_list_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> None:
    tasks = get_active_tasks()
    await update.message.reply_text(list_tasks(tasks))


@require_registration
async def on_edit_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> None:
    args = parse_edit_task_args(update.message.text)
    if args is None:
        await update.message.reply_text(edit_task_usage(), parse_mode=ParseMode.HTML)
        return

    task_name, field, value = args
    task = get_active_task_by_name(task_name)
    if task is None:
        await update.message.reply_text(task_not_found_by_name(task_name))
        return

    db_field = EDITABLE_TASK_PROPS[field]
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
        coerced = coerce_edit_value(db_field, value)
    except ValueError:
        msg = task_invalid_points() if db_field == "points" else task_invalid_frequency()
        await update.message.reply_text(msg)
        return

    result = update_active_task(task.id, **{db_field: coerced})
    await update.message.reply_text(
        update_task_reply(result, task_name, field, old_value, new_value),
        parse_mode=ParseMode.HTML,
    )


@require_registration
async def on_delete_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> None:
    task_name = parse_delete_task_args(update.message.text)
    if task_name is None:
        await update.message.reply_text(delete_task_usage())
        return
    task = get_active_task_by_name(task_name)
    if task is None:
        await update.message.reply_text(
            task_not_found_by_name(task_name), parse_mode=ParseMode.HTML
        )
        return
    result = soft_delete_active_task(task.id)
    await update.message.reply_text(delete_task_reply(result, task_name), parse_mode=ParseMode.HTML)


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


@require_registration
async def on_reminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> None:
    await update.message.reply_text(reminders_crud_explanation(), parse_mode=ParseMode.HTML)


@require_registration
async def on_add_reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> None:
    args = update.message.text.split(maxsplit=1)
    is_add_reminder_command = len(args) < 2 or not args[1].strip()
    if is_add_reminder_command:
        context.user_data["add_reminder_step"] = "message"
        await update.message.reply_text(add_reminder_ask_message())
        return

    args = parse_add_reminder_args(update.message.text)
    if args is None:
        await update.message.reply_text(add_reminder_usage())
        return
    reminder_message, trigger_at, trigger_time, recurrence = args
    result = create_reminder(user.id, reminder_message, trigger_at, trigger_time, recurrence)
    await update.message.reply_text(add_reminder_reply(result))


@require_registration
async def on_list_reminders_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user
) -> None:
    reminders = get_user_reminders(user.id)
    await update.message.reply_text(list_reminders(reminders))


@require_registration
async def on_edit_reminder_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user
) -> None:
    args = update.message.text.split(maxsplit=1)
    is_edit_reminder_command = len(args) < 2 or not args[1].strip()
    if is_edit_reminder_command:
        context.user_data["edit_reminder_step"] = "message"
        await update.message.reply_text(edit_reminder_ask_message())
        return

    args = parse_edit_reminder_args(update.message.text)
    if args is None:
        await update.message.reply_text(edit_reminder_usage(), parse_mode=ParseMode.HTML)
        return

    message, field, value = args
    reminder = get_reminder_by_message(user.id, message)
    if reminder is None:
        await update.message.reply_text(reminder_not_found_by_message(message))
        return

    db_field = EDITABLE_REMINDER_PROPS[field]
    old_value = str(getattr(reminder, field)) if getattr(reminder, field) is not None else "-"
    if field == "recurrence":
        if coerce_recurrence(value) is None:
            await update.message.reply_text(reminder_invalid_recurrence())
            return

    result = update_reminder(reminder.id, user.id, **{db_field: value})
    await update.message.reply_text(
        update_reminder_reply(result, message, field, old_value, value),
        parse_mode=ParseMode.HTML,
    )


@require_registration
async def on_delete_reminder_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user
) -> None:
    args = update.message.text.split(maxsplit=1)
    is_delete_reminder_command = len(args) < 2 or not args[1].strip()
    if is_delete_reminder_command:
        context.user_data["delete_reminder_step"] = "message"
        await update.message.reply_text(delete_reminder_ask_message())
        return

    reminder_message = parse_delete_reminder_args(update.message.text)
    if reminder_message is None:
        await update.message.reply_text(delete_reminder_usage())
        return
    reminder = get_reminder_by_message(reminder_message)
    if reminder is None:
        await update.message.reply_text(
            reminder_not_found_by_message(reminder_message), parse_mode=ParseMode.HTML
        )
        return
    result = delete_reminder_by_message(user.id, reminder_message)
    await update.message.reply_text(
        delete_reminder_reply(result, reminder_message), parse_mode=ParseMode.HTML
    )
