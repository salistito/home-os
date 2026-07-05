from datetime import date

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from apps.bots.telegram.formatters import format_balance, format_morning_message
from core.identity import get_user_by_chat_id, get_users
from modules.tasks.service import get_month_balance, get_pending_assignments


async def on_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    month = date.today().strftime("%Y-%m")
    balance_data = get_month_balance(month)
    names = {user.id: user.name for user in get_users()}
    await update.message.reply_text(format_balance(month, balance_data, names))

async def on_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = get_user_by_chat_id(str(update.effective_chat.id))
    if user is None:
        await update.message.reply_text("No estás registrado.")
        return

    assignments = [
        a
        for a in get_pending_assignments(date.today())
        if a.assignee_user_id == user.id
    ]
    if not assignments:
        await update.message.reply_text("No quedan tareas para hoy.")
        return

    keyboard = [
        [
            InlineKeyboardButton(
                a.task_name, callback_data=f"task_{a.task_id}|{a.task_name}"
            )
        ]
        for a in assignments
    ]
    await update.message.reply_text(
        format_morning_message(user.name, assignments),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
