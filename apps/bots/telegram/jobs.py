from collections import defaultdict
from datetime import date

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, Forbidden

from apps.bots.telegram.messages_es import morning_message, no_assignments_today
from core.identity import get_users
from modules.tasks.service import clear_stale_pending, get_daily_assignments
from modules.tasks.types import Assignment


async def send_daily_assignments(bot: Bot) -> None:
    today = date.today()
    clear_stale_pending(today)
    assignments = get_daily_assignments(today)
    users_by_id = {user.id: user for user in get_users()}

    by_user: dict[str, list[Assignment]] = defaultdict(list)
    for assignment in assignments:
        by_user[assignment.user_id].append(assignment)

    for user in users_by_id.values():
        assignments = by_user.get(user.id, [])
        if assignments:
            message = morning_message(user.name, assignments)
            keyboard = [
                [
                    InlineKeyboardButton(
                        assignment.task_name,
                        callback_data=f"assignment_{assignment.task_id}|{assignment.task_name}",
                    )
                ]
                for assignment in assignments
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            message = no_assignments_today(user.name)
            reply_markup = None

        try:
            await bot.send_message(
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
