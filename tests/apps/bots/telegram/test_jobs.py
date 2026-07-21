import pytest

from datetime import date
from unittest.mock import AsyncMock, patch

from telegram.error import BadRequest, Forbidden

from apps.bots.telegram.jobs import (
    build_assignment_keyboard,
    send_daily_assignments,
    send_day_reminders,
    send_timed_reminders,
)
from modules.reminders.types import Reminder, ReminderRecurrence
from modules.tasks.types import Assignment
from modules.users.types import User


def _make_user(user_id=1, name="Test", role="admin", telegram_chat_id=123456):
    tc_id = str(telegram_chat_id) if telegram_chat_id is not None else None
    return User(
        id=user_id,
        name=name,
        role=role,
        password_hash=None,
        deleted_at=None,
        telegram_chat_id=tc_id,
    )


def _make_assignment(task_id=1, task_name="Task", user_id=1, points=10):
    return Assignment(task_id=task_id, task_name=task_name, user_id=user_id, points=points)


def _make_reminder(
    reminder_id=1,
    user_id=1,
    message="test",
    trigger_at="2026-03-15",
    trigger_time=None,
    recurrence=ReminderRecurrence.NONE,
):
    return Reminder(
        id=reminder_id,
        user_id=user_id,
        message=message,
        trigger_at=trigger_at,
        trigger_time=trigger_time,
        recurrence=recurrence,
        cron_job_id=None,
        created_at="2026-03-14",
    )


class TestSendDailyAssignments:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sends_assignments_to_users(self):
        bot = AsyncMock()
        bot.send_message = AsyncMock()
        user = _make_user()
        assignment = _make_assignment()

        with (
            patch("apps.bots.telegram.jobs.get_today", return_value=date(2026, 3, 15)),
            patch("apps.bots.telegram.jobs.fail_stale_pending_assignments"),
            patch("apps.bots.telegram.jobs.get_daily_assignments", return_value=[assignment]),
            patch("apps.bots.telegram.jobs.get_active_users", return_value=[user]),
        ):
            await send_daily_assignments(bot)

        bot.send_message.assert_called_once()
        call_kwargs = bot.send_message.call_args.kwargs
        assert call_kwargs["chat_id"] == 123456
        assert call_kwargs["reply_markup"] is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_skips_user_without_telegram_chat_id(self):
        bot = AsyncMock()
        bot.send_message = AsyncMock()
        user = _make_user(telegram_chat_id=None)
        assignment = _make_assignment()

        with (
            patch("apps.bots.telegram.jobs.get_today", return_value=date(2026, 3, 15)),
            patch("apps.bots.telegram.jobs.fail_stale_pending_assignments"),
            patch("apps.bots.telegram.jobs.get_daily_assignments", return_value=[assignment]),
            patch("apps.bots.telegram.jobs.get_active_users", return_value=[user]),
        ):
            await send_daily_assignments(bot)

        bot.send_message.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_chat_not_found_skips_gracefully(self):
        bot = AsyncMock()
        bot.send_message = AsyncMock(side_effect=BadRequest("Chat not found"))
        user = _make_user()
        assignment = _make_assignment()

        with (
            patch("apps.bots.telegram.jobs.get_today", return_value=date(2026, 3, 15)),
            patch("apps.bots.telegram.jobs.fail_stale_pending_assignments"),
            patch("apps.bots.telegram.jobs.get_daily_assignments", return_value=[assignment]),
            patch("apps.bots.telegram.jobs.get_active_users", return_value=[user]),
        ):
            await send_daily_assignments(bot)

        bot.send_message.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_bot_blocked_skips_gracefully(self):
        bot = AsyncMock()
        bot.send_message = AsyncMock(side_effect=Forbidden("bot was blocked by the user"))
        user = _make_user()
        assignment = _make_assignment()

        with (
            patch("apps.bots.telegram.jobs.get_today", return_value=date(2026, 3, 15)),
            patch("apps.bots.telegram.jobs.fail_stale_pending_assignments"),
            patch("apps.bots.telegram.jobs.get_daily_assignments", return_value=[assignment]),
            patch("apps.bots.telegram.jobs.get_active_users", return_value=[user]),
        ):
            await send_daily_assignments(bot)

        bot.send_message.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_other_exceptions_propagate(self):
        bot = AsyncMock()
        bot.send_message = AsyncMock(side_effect=RuntimeError("unexpected failure"))
        user = _make_user()
        assignment = _make_assignment()

        with (
            patch("apps.bots.telegram.jobs.get_today", return_value=date(2026, 3, 15)),
            patch("apps.bots.telegram.jobs.fail_stale_pending_assignments"),
            patch("apps.bots.telegram.jobs.get_daily_assignments", return_value=[assignment]),
            patch("apps.bots.telegram.jobs.get_active_users", return_value=[user]),
            pytest.raises(RuntimeError, match="unexpected failure"),
        ):
            await send_daily_assignments(bot)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_user_with_no_assignments_gets_no_assignments_message(self):
        bot = AsyncMock()
        bot.send_message = AsyncMock()
        user = _make_user()

        with (
            patch("apps.bots.telegram.jobs.get_today", return_value=date(2026, 3, 15)),
            patch("apps.bots.telegram.jobs.fail_stale_pending_assignments"),
            patch("apps.bots.telegram.jobs.get_daily_assignments", return_value=[]),
            patch("apps.bots.telegram.jobs.get_active_users", return_value=[user]),
        ):
            await send_daily_assignments(bot)

        bot.send_message.assert_called_once()
        call_kwargs = bot.send_message.call_args.kwargs
        assert call_kwargs["reply_markup"] is None


class TestSendDayReminders:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sends_and_processes(self):
        bot = AsyncMock()
        bot.send_message = AsyncMock()
        user = _make_user()
        reminder = _make_reminder()

        with (
            patch("apps.bots.telegram.jobs.get_due_day_reminders", return_value=[reminder]),
            patch("apps.bots.telegram.jobs.get_active_user_by_id", return_value=user),
            patch("apps.bots.telegram.jobs.process_reminder_states"),
            patch(
                "apps.bots.telegram.jobs.day_reminders_message", return_value="day reminder text"
            ),
        ):
            await send_day_reminders(bot)

        bot.send_message.assert_called_once()
        call_kwargs = bot.send_message.call_args.kwargs
        assert call_kwargs["chat_id"] == 123456

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_user_without_telegram_skips_message_but_processes(self):
        bot = AsyncMock()
        bot.send_message = AsyncMock()
        user = _make_user(telegram_chat_id=None)
        reminder = _make_reminder()

        with (
            patch("apps.bots.telegram.jobs.get_due_day_reminders", return_value=[reminder]),
            patch("apps.bots.telegram.jobs.get_active_user_by_id", return_value=user),
            patch("apps.bots.telegram.jobs.process_reminder_states") as mock_process,
        ):
            await send_day_reminders(bot)

        bot.send_message.assert_not_called()
        mock_process.assert_called_once_with([reminder])

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_send_message_raises_handled(self):
        bot = AsyncMock()
        bot.send_message = AsyncMock(side_effect=BadRequest("Chat not found"))
        user = _make_user()
        reminder = _make_reminder()

        with (
            patch("apps.bots.telegram.jobs.get_due_day_reminders", return_value=[reminder]),
            patch("apps.bots.telegram.jobs.get_active_user_by_id", return_value=user),
            patch("apps.bots.telegram.jobs.process_reminder_states"),
        ):
            await send_day_reminders(bot)

        bot.send_message.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_user_not_found_skips_but_processes(self):
        bot = AsyncMock()
        bot.send_message = AsyncMock()
        reminder = _make_reminder(user_id=99)

        with (
            patch("apps.bots.telegram.jobs.get_due_day_reminders", return_value=[reminder]),
            patch("apps.bots.telegram.jobs.get_active_user_by_id", return_value=None),
            patch("apps.bots.telegram.jobs.process_reminder_states") as mock_process,
        ):
            await send_day_reminders(bot)

        bot.send_message.assert_not_called()
        mock_process.assert_called_once_with([reminder])


class TestSendTimedReminders:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sends_and_processes(self):
        bot = AsyncMock()
        bot.send_message = AsyncMock()
        user = _make_user()
        reminder = _make_reminder(trigger_time="10:30")

        with (
            patch("apps.bots.telegram.jobs.get_due_timed_reminders", return_value=[reminder]),
            patch("apps.bots.telegram.jobs.get_active_user_by_id", return_value=user),
            patch("apps.bots.telegram.jobs.process_reminder_states"),
            patch("apps.bots.telegram.jobs.timed_reminder_message", return_value="timed reminder"),
        ):
            await send_timed_reminders(bot)

        bot.send_message.assert_called_once()
        call_kwargs = bot.send_message.call_args.kwargs
        assert call_kwargs["chat_id"] == 123456

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_user_without_telegram_skips_message_but_processes(self):
        bot = AsyncMock()
        bot.send_message = AsyncMock()
        user = _make_user(telegram_chat_id=None)
        reminder = _make_reminder(trigger_time="10:30")

        with (
            patch("apps.bots.telegram.jobs.get_due_timed_reminders", return_value=[reminder]),
            patch("apps.bots.telegram.jobs.get_active_user_by_id", return_value=user),
            patch("apps.bots.telegram.jobs.process_reminder_states") as mock_process,
        ):
            await send_timed_reminders(bot)

        bot.send_message.assert_not_called()
        mock_process.assert_called_once_with([reminder])

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_send_message_raises_handled(self):
        bot = AsyncMock()
        bot.send_message = AsyncMock(side_effect=Forbidden("bot was blocked by the user"))
        user = _make_user()
        reminder = _make_reminder(trigger_time="10:30")

        with (
            patch("apps.bots.telegram.jobs.get_due_timed_reminders", return_value=[reminder]),
            patch("apps.bots.telegram.jobs.get_active_user_by_id", return_value=user),
            patch("apps.bots.telegram.jobs.process_reminder_states"),
        ):
            await send_timed_reminders(bot)

        bot.send_message.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_user_not_found_skips_but_processes(self):
        bot = AsyncMock()
        bot.send_message = AsyncMock()
        reminder = _make_reminder(user_id=99, trigger_time="10:30")

        with (
            patch("apps.bots.telegram.jobs.get_due_timed_reminders", return_value=[reminder]),
            patch("apps.bots.telegram.jobs.get_active_user_by_id", return_value=None),
            patch("apps.bots.telegram.jobs.process_reminder_states") as mock_process,
        ):
            await send_timed_reminders(bot)

        bot.send_message.assert_not_called()
        mock_process.assert_called_once_with([reminder])


@pytest.mark.unit
def test_build_assignment_keyboard_empty_returns_none():
    result = build_assignment_keyboard([])
    assert result is None
