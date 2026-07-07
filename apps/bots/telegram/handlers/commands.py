from datetime import date

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from apps.bots.telegram.handlers.messages import build_task_list
from apps.bots.telegram.messages_es import (
    balance,
    no_pending_tasks,
    start_welcome,
    user_not_registered,
)
from core.identity import get_user_by_chat_id, get_users
from modules.tasks.service import get_daily_assignments, get_month_balance


async def on_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(start_welcome())


async def on_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await on_start_command(update, context)


async def on_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    month = date.today().strftime("%Y-%m")
    balance_data = get_month_balance(month)
    names = {user.id: user.name for user in get_users()}
    await update.message.reply_text(balance(month, balance_data, names))


async def on_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = get_user_by_chat_id(str(update.effective_chat.id))
    if user is None:
        await update.message.reply_text(user_not_registered())
        return

    today = date.today()
    if not any(a.assignee_user_id == user.id for a in get_daily_assignments(today)):
        await update.message.reply_text(no_pending_tasks())
        return

    old_message_id = context.user_data.get("tasks_message_id")
    if old_message_id:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=old_message_id
            )
        except BadRequest:
            pass

    text, reply_markup = build_task_list(user, today)
    sent = await update.message.reply_text(text, reply_markup=reply_markup)
    context.user_data["tasks_message_id"] = sent.message_id
