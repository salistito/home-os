import pytest

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from apps.bots.telegram.handlers.utils.reminders import (
    parse_relative_time,
    parse_absolute_date,
    parse_add_reminder_args,
    parse_edit_reminder_args,
    parse_delete_reminder_args,
    coerce_recurrence,
    add_reminder_reply,
    update_reminder_reply,
    delete_reminder_reply,
    handle_add_reminder_wizard,
    handle_edit_reminder_wizard,
    handle_delete_reminder_wizard,
)
from modules.reminders.types import (
    Reminder,
    ReminderOperationResult,
    ReminderOperationStatus,
    ReminderRecurrence,
)

FROZEN_NOW = datetime(2026, 3, 15, 10, 30, 0)


def _make_reminder(
    reminder_id=1,
    user_id=1,
    message="test",
    trigger_at="2026-12-01",
    trigger_time=None,
    recurrence=ReminderRecurrence.NONE,
    cron_job_id=None,
    created_at="2026-01-01",
):
    return Reminder(
        id=reminder_id,
        user_id=user_id,
        message=message,
        trigger_at=trigger_at,
        trigger_time=trigger_time,
        recurrence=recurrence,
        cron_job_id=cron_job_id,
        created_at=created_at,
    )


def _make_result(reminder=None, status=ReminderOperationStatus.OK):
    return ReminderOperationResult(reminder=reminder, status=status)


class TestParseRelativeTime:
    @pytest.mark.unit
    def test_hours(self):
        with patch("apps.bots.telegram.handlers.utils.reminders.get_now", return_value=FROZEN_NOW):
            result = parse_relative_time("3h")
        assert result == ("2026-03-15", "13:30")

    @pytest.mark.unit
    def test_minutes(self):
        with patch("apps.bots.telegram.handlers.utils.reminders.get_now", return_value=FROZEN_NOW):
            result = parse_relative_time("30m")
        assert result == ("2026-03-15", "11:00")

    @pytest.mark.unit
    def test_hours_and_minutes(self):
        with patch("apps.bots.telegram.handlers.utils.reminders.get_now", return_value=FROZEN_NOW):
            result = parse_relative_time("1h30m")
        assert result == ("2026-03-15", "12:00")

    @pytest.mark.unit
    def test_days(self):
        with patch("apps.bots.telegram.handlers.utils.reminders.get_now", return_value=FROZEN_NOW):
            result = parse_relative_time("2d")
        assert result == ("2026-03-17", "10:30")

    @pytest.mark.unit
    def test_weeks(self):
        with patch("apps.bots.telegram.handlers.utils.reminders.get_now", return_value=FROZEN_NOW):
            result = parse_relative_time("1w")
        assert result == ("2026-03-22", "10:30")

    @pytest.mark.unit
    def test_invalid(self):
        with patch("apps.bots.telegram.handlers.utils.reminders.get_now", return_value=FROZEN_NOW):
            assert parse_relative_time("invalid") is None

    @pytest.mark.unit
    def test_invalid_unit(self):
        with patch("apps.bots.telegram.handlers.utils.reminders.get_now", return_value=FROZEN_NOW):
            assert parse_relative_time("3x") is None


class TestParseAbsoluteDate:
    @pytest.mark.unit
    def test_date_only(self):
        assert parse_absolute_date("2026-03-15") == ("2026-03-15", None)

    @pytest.mark.unit
    def test_date_and_time(self):
        assert parse_absolute_date("2026-03-15 14:30") == ("2026-03-15", "14:30")

    @pytest.mark.unit
    def test_invalid_date(self):
        assert parse_absolute_date("03-15-2026") is None

    @pytest.mark.unit
    def test_invalid_format(self):
        assert parse_absolute_date("invalid") is None

    @pytest.mark.unit
    def test_too_many_parts(self):
        assert parse_absolute_date("2026-03-15 14:30 extra") is None


class TestParseAddReminderArgs:
    @pytest.mark.unit
    def test_relative_time(self):
        with patch("apps.bots.telegram.handlers.utils.reminders.get_now", return_value=FROZEN_NOW):
            result = parse_add_reminder_args("/add_reminder test msg 3h")
        assert result is not None
        message, trigger_at, trigger_time, recurrence = result
        assert message == "test msg"
        assert trigger_at == "2026-03-15"
        assert trigger_time == "13:30"
        assert recurrence == "none"

    @pytest.mark.unit
    def test_relative_time_with_recurrence(self):
        with patch("apps.bots.telegram.handlers.utils.reminders.get_now", return_value=FROZEN_NOW):
            result = parse_add_reminder_args("/add_reminder test msg 3h daily")
        assert result is not None
        message, trigger_at, trigger_time, recurrence = result
        assert message == "test msg"
        assert recurrence == "daily"

    @pytest.mark.unit
    def test_absolute_date(self):
        result = parse_add_reminder_args("/add_reminder test msg 2026-12-01")
        assert result is not None
        message, trigger_at, trigger_time, recurrence = result
        assert message == "test msg"
        assert trigger_at == "2026-12-01"
        assert trigger_time is None
        assert recurrence == "none"

    @pytest.mark.unit
    def test_absolute_date_time(self):
        result = parse_add_reminder_args("/add_reminder test msg 2026-12-01 14:30")
        assert result is not None
        message, trigger_at, trigger_time, recurrence = result
        assert message == "test msg"
        assert trigger_at == "2026-12-01"
        assert trigger_time == "14:30"
        assert recurrence == "none"

    @pytest.mark.unit
    def test_absolute_date_time_with_recurrence(self):
        result = parse_add_reminder_args("/add_reminder test msg 2026-12-01 14:30 weekly")
        assert result is not None
        message, trigger_at, trigger_time, recurrence = result
        assert recurrence == "weekly"

    @pytest.mark.unit
    def test_not_enough_args(self):
        assert parse_add_reminder_args("/add_reminder test") is None

    @pytest.mark.unit
    def test_empty(self):
        assert parse_add_reminder_args("/add_reminder") is None

    @pytest.mark.unit
    def test_invalid_time_format(self):
        assert parse_add_reminder_args("/add_reminder test msg invalid") is None

    @pytest.mark.unit
    def test_recurrence_at_end(self):
        result = parse_add_reminder_args("/add_reminder test msg 2026-12-01 weekly")
        assert result is not None
        assert result[3] == "weekly"


class TestParseEditReminderArgs:
    @pytest.mark.unit
    def test_valid_args(self):
        result = parse_edit_reminder_args("/edit_reminder test message newmsg")
        assert result == ("test", "message", "newmsg")

    @pytest.mark.unit
    def test_not_enough_args(self):
        assert parse_edit_reminder_args("/edit_reminder test message") is None

    @pytest.mark.unit
    def test_field_not_found(self):
        assert parse_edit_reminder_args("/edit_reminder test bad value") is None

    @pytest.mark.unit
    def test_multi_word_message(self):
        result = parse_edit_reminder_args("/edit_reminder my test reminder message newmsg")
        assert result == ("my test reminder", "message", "newmsg")


class TestParseDeleteReminderArgs:
    @pytest.mark.unit
    def test_valid_args(self):
        result = parse_delete_reminder_args("/delete_reminder test msg")
        assert result == "test msg"

    @pytest.mark.unit
    def test_no_args(self):
        assert parse_delete_reminder_args("/delete_reminder") is None


class TestCoerceRecurrence:
    @pytest.mark.unit
    def test_daily(self):
        assert coerce_recurrence("daily") == ReminderRecurrence.DAILY

    @pytest.mark.unit
    def test_none(self):
        assert coerce_recurrence("none") == ReminderRecurrence.NONE

    @pytest.mark.unit
    def test_invalid(self):
        assert coerce_recurrence("invalid") is None

    @pytest.mark.unit
    def test_case_insensitive(self):
        assert coerce_recurrence("DAILY") == ReminderRecurrence.DAILY


class TestAddReminderReply:
    @pytest.mark.unit
    def test_ok(self):
        reminder = _make_reminder()
        result = _make_result(reminder=reminder, status=ReminderOperationStatus.OK)
        reply = add_reminder_reply(result)
        assert reminder.message in reply

    @pytest.mark.unit
    def test_invalid(self):
        result = _make_result(status=ReminderOperationStatus.INVALID)
        assert "Datos" in add_reminder_reply(result)

    @pytest.mark.unit
    def test_past_time(self):
        result = _make_result(status=ReminderOperationStatus.PAST_TIME)
        assert "pasado" in add_reminder_reply(result)

    @pytest.mark.unit
    def test_duplicate_message(self):
        reminder = _make_reminder(message="Dup")
        result = _make_result(reminder=reminder, status=ReminderOperationStatus.DUPLICATE_MESSAGE)
        assert "Dup" in add_reminder_reply(result)


class TestUpdateReminderReply:
    @pytest.mark.unit
    def test_ok(self):
        result = _make_result(status=ReminderOperationStatus.OK)
        reply = update_reminder_reply(result, "test", "message", "old", "new")
        assert "actualizado" in reply or "old" in reply

    @pytest.mark.unit
    def test_not_found(self):
        result = _make_result(status=ReminderOperationStatus.NOT_FOUND)
        reply = update_reminder_reply(result, "missing", "message", "old", "new")
        assert "missing" in reply

    @pytest.mark.unit
    def test_invalid(self):
        result = _make_result(status=ReminderOperationStatus.INVALID)
        reply = update_reminder_reply(result, "test", "message", "old", "new")
        assert "Datos" in reply

    @pytest.mark.unit
    def test_past_time(self):
        result = _make_result(status=ReminderOperationStatus.PAST_TIME)
        reply = update_reminder_reply(result, "test", "message", "old", "new")
        assert "pasado" in reply

    @pytest.mark.unit
    def test_duplicate_message(self):
        reminder = _make_reminder(message="Dup")
        result = _make_result(reminder=reminder, status=ReminderOperationStatus.DUPLICATE_MESSAGE)
        reply = update_reminder_reply(result, "Dup", "message", "old", "Dup")
        assert "Dup" in reply


class TestDeleteReminderReply:
    @pytest.mark.unit
    def test_ok(self):
        result = _make_result(status=ReminderOperationStatus.OK)
        reply = delete_reminder_reply(result, "Test")
        assert "Test" in reply

    @pytest.mark.unit
    def test_not_found(self):
        result = _make_result(status=ReminderOperationStatus.NOT_FOUND)
        reply = delete_reminder_reply(result, "missing")
        assert "missing" in reply


class TestHandleAddReminderWizard:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_step_returns_false(self):
        update = MagicMock()
        context = MagicMock()
        context.user_data = {}
        user = MagicMock()

        result = await handle_add_reminder_wizard(update, context, user)
        assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_message_step_saves_and_asks_time(self):
        update = MagicMock()
        update.message.text = "my reminder"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {"add_reminder_step": "message"}
        user = MagicMock()
        user.id = 1

        with patch(
            "apps.bots.telegram.handlers.utils.reminders.get_reminder_by_message",
            return_value=None,
        ):
            result = await handle_add_reminder_wizard(update, context, user)

        assert result is True
        assert context.user_data["reminder_message"] == "my reminder"
        assert context.user_data["add_reminder_step"] == "time"
        update.message.reply_text.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_message_step_duplicate_shows_error(self):
        update = MagicMock()
        update.message.text = "dup"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {"add_reminder_step": "message"}
        user = MagicMock()
        user.id = 1
        existing = _make_reminder(message="dup")

        with patch(
            "apps.bots.telegram.handlers.utils.reminders.get_reminder_by_message",
            return_value=existing,
        ):
            result = await handle_add_reminder_wizard(update, context, user)

        assert result is True
        update.message.reply_text.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_time_step_creates_reminder_on_valid_input(self):
        update = MagicMock()
        update.message.text = "3h"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {
            "add_reminder_step": "time",
            "reminder_message": "test reminder",
        }
        user = MagicMock()
        user.id = 1

        with (
            patch(
                "apps.bots.telegram.handlers.utils.reminders.get_now",
                return_value=FROZEN_NOW,
            ),
            patch("apps.bots.telegram.handlers.utils.reminders.is_past", return_value=False),
        ):
            result = await handle_add_reminder_wizard(update, context, user)

        assert result is True
        assert context.user_data["add_reminder_step"] == "recurrence"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_time_step_invalid_shows_error(self):
        update = MagicMock()
        update.message.text = "invalid"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {
            "add_reminder_step": "time",
        }
        user = MagicMock()

        with patch(
            "apps.bots.telegram.handlers.utils.reminders.get_now",
            return_value=FROZEN_NOW,
        ):
            result = await handle_add_reminder_wizard(update, context, user)

        assert result is True
        update.message.reply_text.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_time_step_past_shows_error(self):
        update = MagicMock()
        update.message.text = "3h"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {
            "add_reminder_step": "time",
        }
        user = MagicMock()

        with (
            patch(
                "apps.bots.telegram.handlers.utils.reminders.get_now",
                return_value=FROZEN_NOW,
            ),
            patch("apps.bots.telegram.handlers.utils.reminders.is_past", return_value=True),
        ):
            result = await handle_add_reminder_wizard(update, context, user)

        assert result is True
        update.message.reply_text.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_recurrence_step_valid_creates(self):
        update = MagicMock()
        update.message.text = "daily"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {
            "add_reminder_step": "recurrence",
            "reminder_message": "test reminder",
            "reminder_trigger_at": "2026-12-01",
            "reminder_trigger_time": None,
        }
        user = MagicMock()
        user.id = 1

        reminder = _make_reminder()
        result_obj = _make_result(reminder=reminder)

        with patch(
            "apps.bots.telegram.handlers.utils.reminders.create_reminder",
            return_value=result_obj,
        ):
            result = await handle_add_reminder_wizard(update, context, user)

        assert result is True
        update.message.reply_text.assert_called_once()
        assert "add_reminder_step" not in context.user_data

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_recurrence_step_invalid_shows_error(self):
        update = MagicMock()
        update.message.text = "bad_recurrence"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {
            "add_reminder_step": "recurrence",
        }
        user = MagicMock()

        result = await handle_add_reminder_wizard(update, context, user)

        assert result is True
        update.message.reply_text.assert_called_once()


class TestHandleEditReminderWizard:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_step_returns_false(self):
        update = MagicMock()
        context = MagicMock()
        context.user_data = {}
        user = MagicMock()

        result = await handle_edit_reminder_wizard(update, context, user)
        assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_message_step_finds_reminder(self):
        update = MagicMock()
        update.message.text = "my reminder"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {"edit_reminder_step": "message"}
        user = MagicMock()
        user.id = 1
        reminder = _make_reminder(message="my reminder")

        with patch(
            "apps.bots.telegram.handlers.utils.reminders.get_reminder_by_message",
            return_value=reminder,
        ):
            result = await handle_edit_reminder_wizard(update, context, user)

        assert result is True
        assert context.user_data["edit_reminder_step"] == "field"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_message_step_not_found(self):
        update = MagicMock()
        update.message.text = "missing"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {"edit_reminder_step": "message"}
        user = MagicMock()
        user.id = 1

        with patch(
            "apps.bots.telegram.handlers.utils.reminders.get_reminder_by_message",
            return_value=None,
        ):
            result = await handle_edit_reminder_wizard(update, context, user)

        assert result is True
        update.message.reply_text.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_field_step_valid(self):
        update = MagicMock()
        update.message.text = "message"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {"edit_reminder_step": "field"}
        user = MagicMock()

        result = await handle_edit_reminder_wizard(update, context, user)

        assert result is True
        assert context.user_data["edit_reminder_step"] == "value"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_field_step_invalid(self):
        update = MagicMock()
        update.message.text = "bad_field"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {"edit_reminder_step": "field"}
        user = MagicMock()

        result = await handle_edit_reminder_wizard(update, context, user)

        assert result is True
        update.message.reply_text.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_value_step_updates(self):
        update = MagicMock()
        update.message.text = "new msg"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {
            "edit_reminder_step": "value",
            "edit_reminder_message": "old msg",
            "edit_reminder_field": "message",
        }
        user = MagicMock()
        user.id = 1
        reminder = _make_reminder(message="old msg")
        result_obj = _make_result(reminder=reminder)

        with (
            patch(
                "apps.bots.telegram.handlers.utils.reminders.get_reminder_by_message",
                return_value=reminder,
            ),
            patch(
                "apps.bots.telegram.handlers.utils.reminders.update_reminder",
                return_value=result_obj,
            ),
        ):
            result = await handle_edit_reminder_wizard(update, context, user)

        assert result is True
        update.message.reply_text.assert_called_once()
        assert "edit_reminder_step" not in context.user_data


class TestHandleDeleteReminderWizard:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_step_returns_false(self):
        update = MagicMock()
        context = MagicMock()
        context.user_data = {}
        user = MagicMock()

        result = await handle_delete_reminder_wizard(update, context, user)
        assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_deletes_reminder(self):
        update = MagicMock()
        update.message.text = "my reminder"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {"delete_reminder_step": "message"}
        user = MagicMock()
        user.id = 1
        reminder = _make_reminder(message="my reminder")
        result_obj = _make_result(reminder=reminder)

        with (
            patch(
                "apps.bots.telegram.handlers.utils.reminders.get_reminder_by_message",
                return_value=reminder,
            ),
            patch(
                "apps.bots.telegram.handlers.utils.reminders.delete_reminder_by_message",
                return_value=result_obj,
            ),
        ):
            result = await handle_delete_reminder_wizard(update, context, user)

        assert result is True
        update.message.reply_text.assert_called_once()
        assert "delete_reminder_step" not in context.user_data

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_not_found(self):
        update = MagicMock()
        update.message.text = "missing"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {"delete_reminder_step": "message"}
        user = MagicMock()
        user.id = 1

        with patch(
            "apps.bots.telegram.handlers.utils.reminders.get_reminder_by_message",
            return_value=None,
        ):
            result = await handle_delete_reminder_wizard(update, context, user)

        assert result is True
        update.message.reply_text.assert_called_once()
        assert "delete_reminder_step" not in context.user_data
