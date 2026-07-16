from collections import defaultdict

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, Forbidden

from apps.bots.telegram.messages_es import (
    day_reminders_message,
    morning_message,
    no_assignments_today,
    timed_reminder_message,
)
from core.identity import get_user_by_id, get_users
from core.utils.date import get_today
from modules.reminders.service import (
    advance_recurrence,
    delete_reminder,
    get_due_day_reminders,
    get_due_timed_reminders,
)
from modules.tasks.service import fail_stale_pending_assignments, get_daily_assignments
from modules.tasks.types import Assignment


async def send_daily_assignments(bot: Bot) -> None:
    today = get_today()
    fail_stale_pending_assignments(today)
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


async def send_day_reminders(bot: Bot) -> None:
    day_reminders = get_due_day_reminders()
    day_reminders_by_user: dict[str, list] = defaultdict(list)
    for reminder in day_reminders:
        day_reminders_by_user[reminder.user_id].append(reminder)

    for user_id, reminders in day_reminders_by_user.items():
        user = get_user_by_id(user_id)
        if not user:
            continue

        try:
            await bot.send_message(
                chat_id=int(user.telegram_chat_id),
                text=day_reminders_message(reminders),
            )
            for reminder in reminders:
                if reminder.recurrence.value == "none":
                    delete_reminder(reminder.id, reminder.user_id)
                else:
                    advance_recurrence(reminder)
        except (BadRequest, Forbidden):
            pass


async def send_timed_reminders(bot: Bot) -> None:
    timed_reminders = get_due_timed_reminders()
    for reminder in timed_reminders:
        user = get_user_by_id(reminder.user_id)
        if not user:
            continue

        try:
            await bot.send_message(
                chat_id=int(user.telegram_chat_id),
                text=timed_reminder_message(reminder),
            )
            if reminder.recurrence.value == "none":
                delete_reminder(reminder.id, reminder.user_id)
            else:
                advance_recurrence(reminder)
        except (BadRequest, Forbidden):
            pass
