from collections import defaultdict

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, Forbidden

from apps.bots.telegram.messages_es import (
    day_reminders_message,
    morning_message,
    no_assignments_today,
    timed_reminder_message,
)
from core.utils.date import get_today
from modules.reminders.service import (
    get_due_day_reminders,
    get_due_timed_reminders,
    process_reminder_states,
)
from modules.tasks.service import fail_stale_pending_assignments, get_daily_assignments
from modules.tasks.types import Assignment
from modules.users.repository import get_active_users, get_active_user_by_id


def build_assignment_keyboard(assignments: list[Assignment]) -> InlineKeyboardMarkup | None:
    if not assignments:
        return None
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    a.task_name,
                    callback_data=f"assignment_{a.task_id}|{a.task_name}",
                )
            ]
            for a in assignments
        ]
    )


async def send_daily_assignments(bot: Bot) -> None:
    today = get_today()
    fail_stale_pending_assignments(today)
    today_assignments = get_daily_assignments(today)

    active_users_with_telegram = {
        user.id: user for user in get_active_users() if user.telegram_chat_id is not None
    }
    assignments_by_user: dict[int, list[Assignment]] = defaultdict(list)
    for assignment in today_assignments:
        assignments_by_user[assignment.user_id].append(assignment)

    for user in active_users_with_telegram.values():
        user_assignments = assignments_by_user.get(user.id, [])
        if user_assignments:
            message = morning_message(user.name, user_assignments)
            reply_markup = build_assignment_keyboard(user_assignments)
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
    day_reminders_by_user: dict[int, list] = defaultdict(list)
    for reminder in day_reminders:
        day_reminders_by_user[reminder.user_id].append(reminder)

    for user_id, reminders in day_reminders_by_user.items():
        user = get_active_user_by_id(user_id)
        if not user or user.telegram_chat_id is None:
            process_reminder_states(reminders)
            continue

        try:
            await bot.send_message(
                chat_id=int(user.telegram_chat_id),
                text=day_reminders_message(reminders),
            )
            process_reminder_states(reminders)
        except (TypeError, BadRequest, Forbidden):
            pass


async def send_timed_reminders(bot: Bot) -> None:
    timed_reminders = get_due_timed_reminders()
    for reminder in timed_reminders:
        user = get_active_user_by_id(reminder.user_id)
        if not user or user.telegram_chat_id is None:
            process_reminder_states([reminder])
            continue

        try:
            await bot.send_message(
                chat_id=int(user.telegram_chat_id),
                text=timed_reminder_message(reminder),
            )
            process_reminder_states([reminder])
        except (TypeError, BadRequest, Forbidden):
            pass
