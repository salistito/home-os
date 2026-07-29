from datetime import date

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from apps.bots.telegram.handlers.utils.reminders import (
    handle_add_reminder_wizard,
    handle_delete_reminder_wizard,
    handle_edit_reminder_wizard,
)
from apps.bots.telegram.messages_es import (
    assignment_already_done,
    assignment_not_assigned_to_user,
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


async def _send_message(bot, chat_id: str, text: str, reply_markup=None):
    return await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)


async def _delete_message(bot, chat_id: str, message_id: int) -> None:
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except BadRequest:
        pass


async def _replace_message(
    bot, chat_id: str, old_message_id: int | None, text: str, reply_markup=None
):
    if old_message_id is not None:
        await _delete_message(bot, chat_id, old_message_id)
    return await _send_message(bot, chat_id, text, reply_markup)


async def _answer_callback_query(query, text: str | None = None) -> None:
    try:
        await query.answer(text)
    except BadRequest:
        pass


def build_assignment_keyboard(assignments) -> InlineKeyboardMarkup | None:
    if not assignments:
        return None
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    a.task_name, callback_data=f"assignment_{a.task_id}|{a.task_name}"
                )
            ]
            for a in assignments
        ]
    )


def build_assignment_message(user, today: date) -> tuple[str, InlineKeyboardMarkup | None]:
    all_assignments = [a for a in get_daily_assignments(today) if a.user_id == user.id]
    pending_ids = {a.task_id for a in get_pending_daily_assignments(today) if a.user_id == user.id}
    completed_ids = {a.task_id for a in all_assignments if a.task_id not in pending_ids}
    pending_assignments = [a for a in all_assignments if a.task_id not in completed_ids]
    reply_markup = build_assignment_keyboard(pending_assignments)
    return assignments_list(all_assignments, completed_ids), reply_markup


async def replace_assignment_message(
    telegram_chat_id: str, user, today: date, context: ContextTypes.DEFAULT_TYPE, prefix: str = ""
):
    old_message_id = context.user_data.get("assignments_message_id")
    text, reply_markup = build_assignment_message(user, today)
    if prefix:
        text = prefix + "\n\n" + text
    sent = await _replace_message(context.bot, telegram_chat_id, old_message_id, text, reply_markup)
    context.user_data["assignments_message_id"] = sent.message_id


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_chat_id = str(update.effective_chat.id)
    text = html_escape(update.message.text)

    user = get_active_user_by_telegram_chat_id(telegram_chat_id)
    if user is None:
        users_exist = len(get_users()) > 0
        await update.message.reply_text(telegram_chat_id_not_registered(users_exist))
        return

    if await handle_add_reminder_wizard(update, context, user):
        return
    if await handle_edit_reminder_wizard(update, context, user):
        return
    if await handle_delete_reminder_wizard(update, context, user):
        return

    today = get_today()
    result = mark_assignment_done(text, user.id, today)

    if result.status == AssignmentCompletionStatus.NOT_FOUND:
        await update.message.reply_text(assignment_not_found(text))
        return

    if result.status == AssignmentCompletionStatus.ALREADY_DONE:
        await update.message.reply_text(assignment_already_done(result.task_name))
        return

    await replace_assignment_message(telegram_chat_id, user, today, context)


async def on_assignment_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    telegram_chat_id = str(query.from_user.id)
    old_message_id = query.message.message_id
    _, task_name = query.data.split("|")

    user = get_active_user_by_telegram_chat_id(telegram_chat_id)
    if user is None:
        await _answer_callback_query(query)
        sent = await _replace_message(
            context.bot,
            telegram_chat_id,
            old_message_id,
            telegram_chat_id_not_registered(len(get_users()) > 0),
        )
        context.user_data["assignments_message_id"] = sent.message_id
        return

    today = get_today()
    result = mark_assignment_done(task_name, user.id, today, must_be_assigned_to_user=True)

    if result.status == AssignmentCompletionStatus.NOT_FOUND:
        await _answer_callback_query(query)
        sent = await _replace_message(
            context.bot,
            telegram_chat_id,
            old_message_id,
            assignment_not_found(task_name),
        )
        context.user_data["assignments_message_id"] = sent.message_id
        return

    answer_text = None
    prefix = None
    if result.status == AssignmentCompletionStatus.ALREADY_DONE:
        answer_text = assignment_already_done(result.task_name)
    elif result.status == AssignmentCompletionStatus.NOT_ASSIGNED:
        prefix = assignment_not_assigned_to_user()

    await _answer_callback_query(query, answer_text)

    text, reply_markup = build_assignment_message(user, today)
    if prefix:
        text = prefix + "\n\n" + text

    sent = await _replace_message(
        context.bot,
        telegram_chat_id,
        old_message_id,
        text,
        reply_markup=reply_markup,
    )
    context.user_data["assignments_message_id"] = sent.message_id
