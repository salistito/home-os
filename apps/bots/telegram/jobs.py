from collections import defaultdict
from datetime import date

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from apps.bots.telegram.formatters import format_morning_message
from core.identity import get_users
from modules.tasks.service import clear_stale_pending, get_daily_assignments
from modules.tasks.types import Assignment


async def send_daily_assignments(context: ContextTypes.DEFAULT_TYPE) -> None:
    today = date.today()
    yesterday = today.fromordinal(today.toordinal() - 1)
    clear_stale_pending(yesterday) # TODO: Fix this. If it's executed after 12:00 AM, it will mark tasks scheduled for yesterday as failed.
    assignments = get_daily_assignments(today)
    users_by_id = {user.id: user for user in get_users()}

    by_user: dict[str, list[Assignment]] = defaultdict(list)
    for assignment in assignments:
        by_user[assignment.assignee_user_id].append(assignment)

    for user_id, tasks in by_user.items():
        user = users_by_id.get(user_id)
        if user is None:
            continue
        message = format_morning_message(user.name, tasks)
        
        keyboard = [
            [InlineKeyboardButton(task.task_name, callback_data=f"task_{task.task_id}|{task.task_name}")]
            for task in tasks
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.send_message(
                chat_id=int(user.telegram_chat_id),
                text=message,
                reply_markup=reply_markup,
            )
        except BadRequest as e:
            if "Chat not found" in str(e):
                continue
            raise
