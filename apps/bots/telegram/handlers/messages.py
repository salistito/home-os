import logging
from datetime import date

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from apps.bots.telegram.messages_es import (
    task_already_done,
    task_not_found,
    tasks_list,
    tasks_updated,
    user_not_registered,
)
from core.identity import get_user_by_chat_id
from modules.tasks.service import get_daily_assignments, get_pending_assignments, mark_task_done
from modules.tasks.types import MarkTaskStatus

logger = logging.getLogger(__name__)


async def _answer_query(query, text: str | None = None) -> None:
    try:
        await query.answer(text)
    except BadRequest:
        logger.warning("callback query expired, continuing anyway")


def build_task_list(user, today: date) -> tuple[str, InlineKeyboardMarkup | None]:
    all_tasks = [a for a in get_daily_assignments(today) if a.assignee_user_id == user.id]
    pending_ids = {
        a.task_id for a in get_pending_assignments(today) if a.assignee_user_id == user.id
    }
    completed_ids = {a.task_id for a in all_tasks if a.task_id not in pending_ids}

    keyboard = [
        [InlineKeyboardButton(a.task_name, callback_data=f"task_{a.task_id}|{a.task_name}")]
        for a in all_tasks
        if a.task_id not in completed_ids
    ]
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    return tasks_list(all_tasks, completed_ids), reply_markup


async def _replace_task_list(
    chat_id: str, user, today: date, context: ContextTypes.DEFAULT_TYPE, prefix: str = ""
):
    old_message_id = context.user_data.get("tasks_message_id")
    if old_message_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=old_message_id)
        except BadRequest:
            pass

    text, reply_markup = build_task_list(user, today)
    if prefix:
        text = prefix + "\n\n" + text
    sent = await context.bot.send_message(
        chat_id=int(chat_id), text=text, reply_markup=reply_markup
    )
    context.user_data["tasks_message_id"] = sent.message_id


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    text = update.message.text

    user = get_user_by_chat_id(chat_id)
    if user is None:
        await update.message.reply_text(user_not_registered())
        return

    today = date.today()
    result = mark_task_done(text, user.id, today)

    if result.status == MarkTaskStatus.NOT_FOUND:
        await update.message.reply_text(task_not_found(text))
        return

    if result.status == MarkTaskStatus.ALREADY_DONE:
        await update.message.reply_text(task_already_done(result.task_name))

    prefix = tasks_updated() if result.status == MarkTaskStatus.OK else ""
    await _replace_task_list(chat_id, user, today, context, prefix=prefix)


async def on_task_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    chat_id = str(query.from_user.id)
    _, task_name = query.data.split("|")

    user = get_user_by_chat_id(chat_id)
    if user is None:
        await _answer_query(query)
        await query.edit_message_text(user_not_registered())
        return

    today = date.today()
    result = mark_task_done(task_name, user.id, today)

    if result.status == MarkTaskStatus.NOT_FOUND:
        await _answer_query(query)
        await query.edit_message_text(task_not_found(task_name))
        return

    answer_text = task_already_done(result.task_name) if result.status == MarkTaskStatus.ALREADY_DONE else None
    await _answer_query(query, answer_text)

    text, reply_markup = build_task_list(user, today)
    if result.status == MarkTaskStatus.OK:
        text = tasks_updated() + "\n\n" + text
    await query.edit_message_text(text, reply_markup=reply_markup)
