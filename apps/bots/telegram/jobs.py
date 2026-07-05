from collections import defaultdict
from datetime import date

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, Forbidden
from telegram.ext import ContextTypes

from apps.bots.telegram.formatters import format_morning_message
from core.identity import get_users
from modules.tasks.service import clear_stale_pending, get_daily_assignments
from modules.tasks.types import Assignment


async def send_daily_assignments(context: ContextTypes.DEFAULT_TYPE) -> None:
    today = date.today()
    clear_stale_pending(today)
    assignments = get_daily_assignments(today)
    users_by_id = {user.id: user for user in get_users()}

    by_user: dict[str, list[Assignment]] = defaultdict(list)
    for assignment in assignments:
        by_user[assignment.assignee_user_id].append(assignment)

    for user in users_by_id.values():
        tasks = by_user.get(user.id, [])
        if tasks:
            message = format_morning_message(user.name, tasks)
            keyboard = [
                [
                    InlineKeyboardButton(
                        task.task_name,
                        callback_data=f"task_{task.task_id}|{task.task_name}",
                    )
                ]
                for task in tasks
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            message = f"¡No tienes tareas pendientes hoy, {user.name}! Felicitaciones 🎉."
            reply_markup = None

        try:
            await context.bot.send_message(
                chat_id=int(user.telegram_chat_id),
                text=message,
                reply_markup=reply_markup,
            )
        except Exception as e:
            if isinstance(e, BadRequest) and "Chat not found" in str(e):
                continue
            if isinstance(e, Forbidden) and "bot was blocked by the user" in str(e):
                continue
            raise
