import logging

from datetime import date

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from apps.bots.telegram.handlers.utils.reminders import (
    handle_add_reminder_wizard,
    handle_edit_reminder_wizard,
    handle_delete_reminder_wizard,
)
from apps.bots.telegram.messages_es import (
    assignment_already_done,
    assignment_not_found,
    assignments_list,
    telegram_chat_id_not_registered,
)
from core.utils.date import get_today
from core.utils.string import html_escape
from modules.tasks.service import (
    get_daily_assignments,
    get_pending_daily_assignments,
    mark_assignment_done,
)
from modules.tasks.types import AssignmentCompletionStatus
from modules.users.repository import get_active_user_by_telegram_chat_id, get_users

logger = logging.getLogger(__name__)


async def answer_query(query, text: str | None = None) -> None:
    try:
        await query.answer(text)
    except BadRequest:
        logger.warning("callback query expired, continuing anyway")


def build_assignment_list(user, today: date) -> tuple[str, InlineKeyboardMarkup | None]:
    all_assignments = [a for a in get_daily_assignments(today) if a.user_id == user.id]
    pending_ids = {a.task_id for a in get_pending_daily_assignments(today) if a.user_id == user.id}
    completed_ids = {a.task_id for a in all_assignments if a.task_id not in pending_ids}

    keyboard = [
        [InlineKeyboardButton(a.task_name, callback_data=f"assignment_{a.task_id}|{a.task_name}")]
        for a in all_assignments
        if a.task_id not in completed_ids
    ]
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    return assignments_list(all_assignments, completed_ids), reply_markup


async def replace_assignment_list(
    telegram_chat_id: str, user, today: date, context: ContextTypes.DEFAULT_TYPE, prefix: str = ""
):
    old_message_id = context.user_data.get("assignments_message_id")
    if old_message_id:
        try:
            await context.bot.delete_message(chat_id=telegram_chat_id, message_id=old_message_id)
        except BadRequest:
            pass

    text, reply_markup = build_assignment_list(user, today)
    if prefix:
        text = prefix + "\n\n" + text
    sent = await context.bot.send_message(
        chat_id=int(telegram_chat_id), text=text, reply_markup=reply_markup
    )
    context.user_data["assignments_message_id"] = sent.message_id


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_chat_id = str(update.effective_chat.id)
    text = html_escape(update.message.text)

    user = get_active_user_by_telegram_chat_id(telegram_chat_id)
    if user is None:
        users_exist = len(get_users()) > 0
        await update.message.reply_text(telegram_chat_id_not_registered(users_exist))
        return

    # Wizards
    if await handle_add_reminder_wizard(update, context, user):
        return
    if await handle_edit_reminder_wizard(update, context, user):
        return
    if await handle_delete_reminder_wizard(update, context, user):
        return

    # Assignments flow
    today = get_today()
    result = mark_assignment_done(text, user.id, today)

    if result.status == AssignmentCompletionStatus.NOT_FOUND:
        await update.message.reply_text(assignment_not_found(text))
        return

    if result.status == AssignmentCompletionStatus.ALREADY_DONE:
        await update.message.reply_text(assignment_already_done(result.task_name))
        return

    await replace_assignment_list(telegram_chat_id, user, today, context)


async def on_assignment_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    telegram_chat_id = str(query.from_user.id)
    _, task_name = query.data.split("|")

    user = get_active_user_by_telegram_chat_id(telegram_chat_id)
    if user is None:
        await answer_query(query)
        try:
            users_exist = len(get_users()) > 0
            await query.edit_message_text(telegram_chat_id_not_registered(users_exist))
        except BadRequest:
            pass
        return

    today = get_today()
    result = mark_assignment_done(task_name, user.id, today)

    if result.status == AssignmentCompletionStatus.NOT_FOUND:
        await answer_query(query)
        try:
            await query.edit_message_text(assignment_not_found(task_name))
        except BadRequest:
            pass
        return

    answer_text = (
        assignment_already_done(result.task_name)
        if result.status == AssignmentCompletionStatus.ALREADY_DONE
        else None
    )
    await answer_query(query, answer_text)

    text, reply_markup = build_assignment_list(user, today)
    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except BadRequest:
        pass
