import pytest

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, Message, Chat
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from apps.bots.telegram.handlers.commands import (
    on_start_command,
    on_help_command,
    on_init_home_command,
    on_add_member_command,
    on_join_command,
    on_tasks_command,
    on_add_task_command,
    on_list_tasks_command,
    on_edit_task_command,
    on_delete_task_command,
    on_assignments_command,
    on_balance_command,
    on_reminders_command,
    on_add_reminder_command,
    on_list_reminders_command,
    on_edit_reminder_command,
    on_delete_reminder_command,
)
from apps.bots.telegram.handlers.messages import (
    answer_query,
    build_assignment_list,
    on_assignment_button,
    on_message,
    replace_assignment_list,
)
from modules.reminders.types import (
    Reminder,
    ReminderOperationResult,
    ReminderOperationStatus,
    ReminderRecurrence,
)
from modules.tasks.types import (
    Assignment,
    Task,
    TaskOperationResult,
    TaskOperationStatus,
    AssignmentCompletionResult,
    AssignmentCompletionStatus,
)
from modules.users.errors import UserAlreadyExistsError
from modules.users.types import User, UserRole


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.effective_chat = MagicMock(spec=Chat)
    update.effective_chat.id = 123456
    message = MagicMock(spec=Message)
    message.reply_text = AsyncMock()
    update.message = message
    update.callback_query = None
    return update


@pytest.fixture
def mock_context():
    ctx = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    ctx.user_data = {}
    ctx.bot = MagicMock()
    ctx.bot.delete_message = AsyncMock()
    ctx.bot.send_message = AsyncMock()
    return ctx


def _make_user(
    user_id=1,
    name="Test",
    role="admin",
    password_hash=None,
    deleted_at=None,
    telegram_chat_id="123456",
):
    return User(
        id=user_id,
        name=name,
        role=role,
        password_hash=password_hash,
        deleted_at=deleted_at,
        telegram_chat_id=telegram_chat_id,
    )


def _make_task(task_id=1, name="Task", points=10, frequency_days=None, next_due_date=None):
    return Task(
        id=task_id,
        name=name,
        points=points,
        frequency_days=frequency_days,
        next_due_date=next_due_date,
    )


def _make_task_result(task=None, status=TaskOperationStatus.OK):
    return TaskOperationResult(task=task, status=status)


def _make_assignment(task_id=1, task_name="Task", user_id=1, points=10):
    return Assignment(task_id=task_id, task_name=task_name, user_id=user_id, points=points)


def _make_completion_result(task_name="Task", status=AssignmentCompletionStatus.OK, points=10):
    return AssignmentCompletionResult(task_name=task_name, status=status, points_awarded=points)


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


def _make_reminder_result(reminder=None, status=ReminderOperationStatus.OK):
    return ReminderOperationResult(reminder=reminder, status=status)


class TestOnStartCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sends_welcome_message(self, mock_update, mock_context):
        with patch("apps.bots.telegram.handlers.commands.start_welcome", return_value="Welcome!"):
            await on_start_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Welcome!")


class TestOnHelpCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sends_welcome_message(self, mock_update, mock_context):
        with patch("apps.bots.telegram.handlers.commands.start_welcome", return_value="Welcome!"):
            await on_help_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Welcome!")


class TestOnInitHomeCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_already_initialized_sends_message(self, mock_update, mock_context):
        with (
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[_make_user()]),
            patch(
                "apps.bots.telegram.handlers.commands.init_home_already_initialized",
                return_value="Already init",
            ),
        ):
            await on_init_home_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Already init")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_users_no_args_sends_usage(self, mock_update, mock_context):
        mock_update.message.text = "/init_home"

        with (
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[]),
            patch("apps.bots.telegram.handlers.commands.init_home_usage", return_value="Usage"),
        ):
            await on_init_home_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Usage")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_users_whitespace_name_sends_usage(self, mock_update, mock_context):
        mock_update.message.text = "/init_home   "

        with (
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[]),
            patch("apps.bots.telegram.handlers.commands.init_home_usage", return_value="Usage"),
        ):
            await on_init_home_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Usage")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_users_valid_name_creates_admin(self, mock_update, mock_context):
        user = _make_user(name="Admin User")
        mock_update.message.text = "/init_home Admin User"

        with (
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[]),
            patch(
                "apps.bots.telegram.handlers.commands.register_user", return_value=user
            ) as mock_register,
            patch("apps.bots.telegram.handlers.commands.init_home_success", return_value="Success"),
        ):
            await on_init_home_command(mock_update, mock_context)

        mock_register.assert_called_once_with(
            "Admin User",
            role=UserRole.ADMIN,
            telegram_chat_id="123456",
        )
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_register_user_raises_sends_error(self, mock_update, mock_context):
        mock_update.message.text = "/init_home Admin"

        with (
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[]),
            patch(
                "apps.bots.telegram.handlers.commands.register_user", side_effect=Exception("fail")
            ),
            patch("apps.bots.telegram.handlers.commands.unexpected_error", return_value="Error"),
        ):
            await on_init_home_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Error")


class TestOnAddMemberCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_non_admin_sends_error(self, mock_update, mock_context):
        user = _make_user(role="member")
        mock_update.message.text = "/add_member NewUser"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.add_member_not_admin",
                return_value="Not admin",
            ),
        ):
            await on_add_member_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Not admin")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_args_sends_usage(self, mock_update, mock_context):
        user = _make_user(role="admin")
        mock_update.message.text = "/add_member"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch("apps.bots.telegram.handlers.commands.add_member_usage", return_value="Usage"),
        ):
            await on_add_member_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Usage")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_args_creates_member(self, mock_update, mock_context):
        admin = _make_user(role="admin")
        member = _make_user(user_id=2, name="NewMember", role="member")
        mock_update.message.text = "/add_member NewMember"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=admin,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[admin]),
            patch(
                "apps.bots.telegram.handlers.commands.register_user", return_value=member
            ) as mock_register,
            patch(
                "apps.bots.telegram.handlers.commands.add_member_success", return_value="Success"
            ),
        ):
            await on_add_member_command(mock_update, mock_context)

        mock_register.assert_called_once_with(user_name="NewMember", role=UserRole.MEMBER)
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_duplicate_name_sends_error(self, mock_update, mock_context):
        admin = _make_user(role="admin")
        mock_update.message.text = "/add_member Existing"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=admin,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[admin]),
            patch(
                "apps.bots.telegram.handlers.commands.register_user",
                side_effect=UserAlreadyExistsError(_make_user(name="Existing")),
            ),
            patch(
                "apps.bots.telegram.handlers.commands.user_duplicate_name", return_value="Duplicate"
            ),
        ):
            await on_add_member_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Duplicate")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_not_registered_sends_message(self, mock_update, mock_context):
        mock_update.message.text = "/add_member NewUser"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=None,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[_make_user()]),
            patch(
                "apps.bots.telegram.handlers.commands.telegram_chat_id_not_registered",
                return_value="Not registered",
            ),
        ):
            await on_add_member_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Not registered")


class TestOnJoinCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_already_linked_sends_message(self, mock_update, mock_context):
        user = _make_user(telegram_chat_id="123456")
        mock_update.message.text = "/join Test"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch(
                "apps.bots.telegram.handlers.commands.join_already_linked",
                return_value="Already linked",
            ),
        ):
            await on_join_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Already linked")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_args_sends_usage(self, mock_update, mock_context):
        mock_update.message.text = "/join"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=None,
            ),
            patch("apps.bots.telegram.handlers.commands.join_usage", return_value="Usage"),
        ):
            await on_join_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Usage")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_user_not_found_sends_error(self, mock_update, mock_context):
        mock_update.message.text = "/join Nobody"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=None,
            ),
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_name", return_value=None
            ),
            patch(
                "apps.bots.telegram.handlers.commands.join_user_not_found", return_value="Not found"
            ),
        ):
            await on_join_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Not found")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_user_already_has_chat_sends_error(self, mock_update, mock_context):
        user = _make_user(telegram_chat_id="other_chat")
        mock_update.message.text = "/join Test"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=None,
            ),
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_name", return_value=user
            ),
            patch(
                "apps.bots.telegram.handlers.commands.join_user_already_has_chat",
                return_value="Has chat",
            ),
        ):
            await on_join_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Has chat")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_join_links_account(self, mock_update, mock_context):
        user = _make_user(telegram_chat_id=None)
        mock_update.message.text = "/join Test"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=None,
            ),
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_name", return_value=user
            ),
            patch(
                "apps.bots.telegram.handlers.commands.update_user", return_value=True
            ) as mock_update_user,
            patch("apps.bots.telegram.handlers.commands.join_success", return_value="Joined"),
        ):
            await on_join_command(mock_update, mock_context)

        mock_update_user.assert_called_once_with(user.id, telegram_chat_id="123456")
        mock_update.message.reply_text.assert_called_once_with("Joined")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_user_raises_sends_error(self, mock_update, mock_context):
        user = _make_user(telegram_chat_id=None)
        mock_update.message.text = "/join Test"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=None,
            ),
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_name", return_value=user
            ),
            patch(
                "apps.bots.telegram.handlers.commands.update_user", side_effect=Exception("fail")
            ),
            patch("apps.bots.telegram.handlers.commands.unexpected_error", return_value="Error"),
        ):
            await on_join_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Error")


class TestOnTasksCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sends_tasks_explanation(self, mock_update, mock_context):
        user = _make_user()

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.tasks_crud_explanation",
                return_value="Tasks info",
            ),
        ):
            await on_tasks_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()


class TestOnAddTaskCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_args_sends_usage(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "/add_task"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch("apps.bots.telegram.handlers.commands.parse_add_task_args", return_value=None),
            patch("apps.bots.telegram.handlers.commands.add_task_usage", return_value="Usage"),
        ):
            await on_add_task_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Usage")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_args_creates_task(self, mock_update, mock_context):
        user = _make_user()
        task = _make_task()
        result = _make_task_result(task=task)
        mock_update.message.text = "/add_task MyTask 10"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.parse_add_task_args",
                return_value=("MyTask", 10, None, None),
            ),
            patch("apps.bots.telegram.handlers.commands.create_task", return_value=result),
            patch("apps.bots.telegram.handlers.commands.add_task_reply", return_value="Created"),
        ):
            await on_add_task_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Created")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_next_due_date_with_frequency_uses_today(self, mock_update, mock_context):
        user = _make_user()
        task = _make_task(frequency_days=7)
        result = _make_task_result(task=task)
        today = date(2026, 3, 15)
        mock_update.message.text = "/add_task MyTask 10 7"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.parse_add_task_args",
                return_value=("MyTask", 10, 7, None),
            ),
            patch("apps.bots.telegram.handlers.commands.get_today", return_value=today),
            patch("apps.bots.telegram.handlers.commands.to_db_date", return_value="2026-03-15"),
            patch(
                "apps.bots.telegram.handlers.commands.create_task", return_value=result
            ) as mock_create,
            patch("apps.bots.telegram.handlers.commands.add_task_reply", return_value="Created"),
        ):
            await on_add_task_command(mock_update, mock_context)

        mock_create.assert_called_once_with("MyTask", 10, 7, "2026-03-15")


class TestOnListTasksCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_lists_tasks(self, mock_update, mock_context):
        user = _make_user()
        tasks = [_make_task()]

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch("apps.bots.telegram.handlers.commands.get_active_tasks", return_value=tasks),
            patch("apps.bots.telegram.handlers.commands.list_tasks", return_value="Task list"),
        ):
            await on_list_tasks_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Task list")


class TestOnEditTaskCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_args_sends_usage(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "/edit_task"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch("apps.bots.telegram.handlers.commands.parse_edit_task_args", return_value=None),
            patch("apps.bots.telegram.handlers.commands.edit_task_usage", return_value="Usage"),
        ):
            await on_edit_task_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_task_not_found_sends_error(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "/edit_task MyTask name NewName"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.parse_edit_task_args",
                return_value=("MyTask", "name", "NewName"),
            ),
            patch(
                "apps.bots.telegram.handlers.commands.get_active_task_by_name", return_value=None
            ),
            patch(
                "apps.bots.telegram.handlers.commands.task_not_found_by_name",
                return_value="Not found",
            ),
        ):
            await on_edit_task_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Not found")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_name_update(self, mock_update, mock_context):
        user = _make_user()
        task = _make_task(name="OldName")
        updated_task = _make_task(name="NewName")
        result = _make_task_result(task=updated_task)
        mock_update.message.text = "/edit_task OldName name NewName"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.parse_edit_task_args",
                return_value=("OldName", "name", "NewName"),
            ),
            patch(
                "apps.bots.telegram.handlers.commands.get_active_task_by_name", return_value=task
            ),
            patch("apps.bots.telegram.handlers.commands.EDITABLE_TASK_PROPS", {"name": "name"}),
            patch("apps.bots.telegram.handlers.commands.coerce_edit_value", return_value="NewName"),
            patch("apps.bots.telegram.handlers.commands.update_active_task", return_value=result),
            patch("apps.bots.telegram.handlers.commands.update_task_reply", return_value="Updated"),
        ):
            await on_edit_task_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_points_sends_error(self, mock_update, mock_context):
        user = _make_user()
        task = _make_task()
        mock_update.message.text = "/edit_task MyTask points bad"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.parse_edit_task_args",
                return_value=("MyTask", "points", "bad"),
            ),
            patch(
                "apps.bots.telegram.handlers.commands.get_active_task_by_name", return_value=task
            ),
            patch("apps.bots.telegram.handlers.commands.EDITABLE_TASK_PROPS", {"points": "points"}),
            patch("apps.bots.telegram.handlers.commands.coerce_edit_value", side_effect=ValueError),
            patch(
                "apps.bots.telegram.handlers.commands.task_invalid_points",
                return_value="Invalid points",
            ),
        ):
            await on_edit_task_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Invalid points")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_frequency_sends_error(self, mock_update, mock_context):
        user = _make_user()
        task = _make_task()
        mock_update.message.text = "/edit_task MyTask freq bad"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.parse_edit_task_args",
                return_value=("MyTask", "freq", "bad"),
            ),
            patch(
                "apps.bots.telegram.handlers.commands.get_active_task_by_name", return_value=task
            ),
            patch(
                "apps.bots.telegram.handlers.commands.EDITABLE_TASK_PROPS",
                {"freq": "frequency_days"},
            ),
            patch("apps.bots.telegram.handlers.commands.coerce_edit_value", side_effect=ValueError),
            patch(
                "apps.bots.telegram.handlers.commands.task_invalid_frequency",
                return_value="Invalid freq",
            ),
        ):
            await on_edit_task_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Invalid freq")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_next_due_date_sends_error(self, mock_update, mock_context):
        user = _make_user()
        task = _make_task()
        mock_update.message.text = "/edit_task MyTask next_occurrence bad"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.parse_edit_task_args",
                return_value=("MyTask", "next_occurrence", "bad"),
            ),
            patch(
                "apps.bots.telegram.handlers.commands.get_active_task_by_name", return_value=task
            ),
            patch(
                "apps.bots.telegram.handlers.commands.EDITABLE_TASK_PROPS",
                {"next_occurrence": "next_due_date"},
            ),
            patch("apps.bots.telegram.handlers.commands.format_date", return_value="2026-01-01"),
            patch("apps.bots.telegram.handlers.commands.coerce_edit_value", side_effect=ValueError),
            patch(
                "apps.bots.telegram.handlers.commands.task_invalid_next_due_date",
                return_value="Invalid date",
            ),
        ):
            await on_edit_task_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Invalid date")


class TestOnDeleteTaskCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_args_sends_usage(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "/delete_task"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch("apps.bots.telegram.handlers.commands.parse_delete_task_args", return_value=None),
            patch("apps.bots.telegram.handlers.commands.delete_task_usage", return_value="Usage"),
        ):
            await on_delete_task_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Usage")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_task_not_found_sends_error(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "/delete_task NonExistent"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.parse_delete_task_args",
                return_value="NonExistent",
            ),
            patch(
                "apps.bots.telegram.handlers.commands.get_active_task_by_name", return_value=None
            ),
            patch(
                "apps.bots.telegram.handlers.commands.task_not_found_by_name",
                return_value="Not found",
            ),
        ):
            await on_delete_task_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_delete_succeeds(self, mock_update, mock_context):
        user = _make_user()
        task = _make_task()
        result = _make_task_result(task=task)
        mock_update.message.text = "/delete_task MyTask"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.parse_delete_task_args", return_value="MyTask"
            ),
            patch(
                "apps.bots.telegram.handlers.commands.get_active_task_by_name", return_value=task
            ),
            patch(
                "apps.bots.telegram.handlers.commands.soft_delete_active_task", return_value=result
            ),
            patch("apps.bots.telegram.handlers.commands.delete_task_reply", return_value="Deleted"),
        ):
            await on_delete_task_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()


class TestOnAssignmentsCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_assignments_sends_no_pending(self, mock_update, mock_context):
        user = _make_user()

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch("apps.bots.telegram.handlers.commands.get_today", return_value=date(2026, 3, 15)),
            patch("apps.bots.telegram.handlers.commands.fail_stale_pending_assignments"),
            patch("apps.bots.telegram.handlers.commands.get_daily_assignments", return_value=[]),
            patch(
                "apps.bots.telegram.handlers.commands.no_pending_assignments",
                return_value="No pending",
            ),
        ):
            await on_assignments_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("No pending")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_has_assignments_builds_list(self, mock_update, mock_context):
        user = _make_user()
        assignment = _make_assignment()

        sent_message = MagicMock()
        sent_message.message_id = 999

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch("apps.bots.telegram.handlers.commands.get_today", return_value=date(2026, 3, 15)),
            patch("apps.bots.telegram.handlers.commands.fail_stale_pending_assignments"),
            patch(
                "apps.bots.telegram.handlers.commands.get_daily_assignments",
                return_value=[assignment],
            ),
            patch(
                "apps.bots.telegram.handlers.commands.build_assignment_list",
                return_value=("Assignments text", None),
            ),
        ):
            mock_update.message.reply_text.return_value = sent_message
            await on_assignments_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        assert mock_context.user_data["assignments_message_id"] == 999

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_deletes_previous_assignment_message(self, mock_update, mock_context):
        user = _make_user()
        assignment = _make_assignment()
        mock_context.user_data["assignments_message_id"] = 888

        sent_message = MagicMock()
        sent_message.message_id = 999

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch("apps.bots.telegram.handlers.commands.get_today", return_value=date(2026, 3, 15)),
            patch("apps.bots.telegram.handlers.commands.fail_stale_pending_assignments"),
            patch(
                "apps.bots.telegram.handlers.commands.get_daily_assignments",
                return_value=[assignment],
            ),
            patch(
                "apps.bots.telegram.handlers.commands.build_assignment_list",
                return_value=("Assignments text", None),
            ),
        ):
            mock_update.message.reply_text.return_value = sent_message
            await on_assignments_command(mock_update, mock_context)

        mock_context.bot.delete_message.assert_called_once_with(
            chat_id=123456,
            message_id=888,
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_previous_message_bad_request_handled(self, mock_update, mock_context):
        user = _make_user()
        assignment = _make_assignment()
        mock_context.user_data["assignments_message_id"] = 888
        mock_context.bot.delete_message.side_effect = BadRequest("message to delete not found")

        sent_message = MagicMock()
        sent_message.message_id = 999

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch("apps.bots.telegram.handlers.commands.get_today", return_value=date(2026, 3, 15)),
            patch("apps.bots.telegram.handlers.commands.fail_stale_pending_assignments"),
            patch(
                "apps.bots.telegram.handlers.commands.get_daily_assignments",
                return_value=[assignment],
            ),
            patch(
                "apps.bots.telegram.handlers.commands.build_assignment_list",
                return_value=("Assignments text", None),
            ),
        ):
            mock_update.message.reply_text.return_value = sent_message
            await on_assignments_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        assert mock_context.user_data["assignments_message_id"] == 999


class TestOnBalanceCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sends_balance(self, mock_update, mock_context, frozen_today):
        month_points = {1: 100}
        users = [_make_user()]

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_month_points", return_value=month_points
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=users),
            patch("apps.bots.telegram.handlers.commands.balance", return_value="Balance text"),
        ):
            await on_balance_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Balance text")


class TestOnRemindersCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sends_reminders_explanation(self, mock_update, mock_context):
        user = _make_user()

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.reminders_crud_explanation",
                return_value="Reminders info",
            ),
        ):
            await on_reminders_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()


class TestOnAddReminderCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_args_starts_wizard(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "/add_reminder"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.add_reminder_ask_message",
                return_value="Ask message",
            ),
        ):
            await on_add_reminder_command(mock_update, mock_context)

        assert mock_context.user_data["add_reminder_step"] == "message"
        mock_update.message.reply_text.assert_called_once_with("Ask message")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_args_sends_usage(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "/add_reminder test"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.parse_add_reminder_args", return_value=None
            ),
            patch("apps.bots.telegram.handlers.commands.add_reminder_usage", return_value="Usage"),
        ):
            await on_add_reminder_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Usage")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_args_creates_reminder(self, mock_update, mock_context):
        user = _make_user()
        reminder = _make_reminder()
        result = _make_reminder_result(reminder=reminder)
        mock_update.message.text = "/add_reminder test 2026-12-01 none"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.parse_add_reminder_args",
                return_value=("test", "2026-12-01", None, "none"),
            ),
            patch("apps.bots.telegram.handlers.commands.create_reminder", return_value=result),
            patch(
                "apps.bots.telegram.handlers.commands.add_reminder_reply", return_value="Created"
            ),
        ):
            await on_add_reminder_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Created")


class TestOnListRemindersCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_lists_reminders(self, mock_update, mock_context):
        user = _make_user()
        reminders = [_make_reminder()]

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.get_user_reminders", return_value=reminders
            ),
            patch(
                "apps.bots.telegram.handlers.commands.list_reminders", return_value="Reminder list"
            ),
        ):
            await on_list_reminders_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Reminder list")


class TestOnEditReminderCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_args_starts_wizard(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "/edit_reminder"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.edit_reminder_ask_message",
                return_value="Ask message",
            ),
        ):
            await on_edit_reminder_command(mock_update, mock_context)

        assert mock_context.user_data["edit_reminder_step"] == "message"
        mock_update.message.reply_text.assert_called_once_with("Ask message")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_args_sends_usage(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "/edit_reminder test"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.parse_edit_reminder_args", return_value=None
            ),
            patch("apps.bots.telegram.handlers.commands.edit_reminder_usage", return_value="Usage"),
        ):
            await on_edit_reminder_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reminder_not_found_sends_error(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "/edit_reminder test message newmsg"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.parse_edit_reminder_args",
                return_value=("test", "message", "newmsg"),
            ),
            patch(
                "apps.bots.telegram.handlers.commands.get_reminder_by_message", return_value=None
            ),
            patch(
                "apps.bots.telegram.handlers.commands.reminder_not_found_by_message",
                return_value="Not found",
            ),
        ):
            await on_edit_reminder_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Not found")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_recurrence_sends_error(self, mock_update, mock_context):
        user = _make_user()
        reminder = _make_reminder()
        mock_update.message.text = "/edit_reminder test recurrence invalid"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.parse_edit_reminder_args",
                return_value=("test", "recurrence", "invalid"),
            ),
            patch(
                "apps.bots.telegram.handlers.commands.get_reminder_by_message",
                return_value=reminder,
            ),
            patch(
                "apps.bots.telegram.handlers.commands.EDITABLE_REMINDER_PROPS",
                {"recurrence": "recurrence"},
            ),
            patch("apps.bots.telegram.handlers.commands.coerce_recurrence", return_value=None),
            patch(
                "apps.bots.telegram.handlers.commands.reminder_invalid_recurrence",
                return_value="Invalid rec",
            ),
        ):
            await on_edit_reminder_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Invalid rec")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_update_succeeds(self, mock_update, mock_context):
        user = _make_user()
        reminder = _make_reminder()
        updated = _make_reminder(message="newmsg")
        result = _make_reminder_result(reminder=updated)
        mock_update.message.text = "/edit_reminder test message newmsg"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.parse_edit_reminder_args",
                return_value=("test", "message", "newmsg"),
            ),
            patch(
                "apps.bots.telegram.handlers.commands.get_reminder_by_message",
                return_value=reminder,
            ),
            patch(
                "apps.bots.telegram.handlers.commands.EDITABLE_REMINDER_PROPS",
                {"message": "message"},
            ),
            patch("apps.bots.telegram.handlers.commands.update_reminder", return_value=result),
            patch(
                "apps.bots.telegram.handlers.commands.update_reminder_reply", return_value="Updated"
            ),
        ):
            await on_edit_reminder_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()


class TestOnDeleteReminderCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_args_starts_wizard(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "/delete_reminder"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.delete_reminder_ask_message",
                return_value="Ask message",
            ),
        ):
            await on_delete_reminder_command(mock_update, mock_context)

        assert mock_context.user_data["delete_reminder_step"] == "message"
        mock_update.message.reply_text.assert_called_once_with("Ask message")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_args_sends_usage(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "/delete_reminder test"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.parse_delete_reminder_args", return_value=None
            ),
            patch(
                "apps.bots.telegram.handlers.commands.delete_reminder_usage", return_value="Usage"
            ),
        ):
            await on_delete_reminder_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Usage")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reminder_not_found_sends_error(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "/delete_reminder test"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.parse_delete_reminder_args",
                return_value="test",
            ),
            patch(
                "apps.bots.telegram.handlers.commands.get_reminder_by_message", return_value=None
            ),
            patch(
                "apps.bots.telegram.handlers.commands.reminder_not_found_by_message",
                return_value="Not found",
            ),
        ):
            await on_delete_reminder_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_delete_succeeds(self, mock_update, mock_context):
        user = _make_user()
        reminder = _make_reminder()
        result = _make_reminder_result(reminder=reminder)
        mock_update.message.text = "/delete_reminder test"

        with (
            patch(
                "apps.bots.telegram.handlers.commands.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.commands.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.commands.parse_delete_reminder_args",
                return_value="test",
            ),
            patch(
                "apps.bots.telegram.handlers.commands.get_reminder_by_message",
                return_value=reminder,
            ),
            patch(
                "apps.bots.telegram.handlers.commands.delete_reminder_by_message",
                return_value=result,
            ),
            patch(
                "apps.bots.telegram.handlers.commands.delete_reminder_reply", return_value="Deleted"
            ),
        ):
            await on_delete_reminder_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()


class TestOnMessage:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_user_not_registered_sends_message(self, mock_update, mock_context):
        mock_update.message.text = "some task"

        with (
            patch(
                "apps.bots.telegram.handlers.messages.get_active_user_by_telegram_chat_id",
                return_value=None,
            ),
            patch("apps.bots.telegram.handlers.messages.get_users", return_value=[_make_user()]),
            patch(
                "apps.bots.telegram.handlers.messages.telegram_chat_id_not_registered",
                return_value="Not registered",
            ),
        ):
            await on_message(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Not registered")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_reminder_wizard_handled(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "wizard input"

        with (
            patch(
                "apps.bots.telegram.handlers.messages.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.messages.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.messages.handle_add_reminder_wizard",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            await on_message(mock_update, mock_context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_edit_reminder_wizard_handled(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "wizard input"

        with (
            patch(
                "apps.bots.telegram.handlers.messages.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.messages.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.messages.handle_add_reminder_wizard",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "apps.bots.telegram.handlers.messages.handle_edit_reminder_wizard",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            await on_message(mock_update, mock_context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_reminder_wizard_handled(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "wizard input"

        with (
            patch(
                "apps.bots.telegram.handlers.messages.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.messages.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.messages.handle_add_reminder_wizard",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "apps.bots.telegram.handlers.messages.handle_edit_reminder_wizard",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "apps.bots.telegram.handlers.messages.handle_delete_reminder_wizard",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            await on_message(mock_update, mock_context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_task_not_found_sends_error(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "UnknownTask"
        result = _make_completion_result(status=AssignmentCompletionStatus.NOT_FOUND, points=0)

        with (
            patch(
                "apps.bots.telegram.handlers.messages.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.messages.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.messages.handle_add_reminder_wizard",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "apps.bots.telegram.handlers.messages.handle_edit_reminder_wizard",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "apps.bots.telegram.handlers.messages.handle_delete_reminder_wizard",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch("apps.bots.telegram.handlers.messages.get_today", return_value=date(2026, 3, 15)),
            patch("apps.bots.telegram.handlers.messages.mark_assignment_done", return_value=result),
            patch(
                "apps.bots.telegram.handlers.messages.assignment_not_found",
                return_value="Not found",
            ),
        ):
            await on_message(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Not found")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_task_already_done_sends_error(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "DoneTask"
        result = _make_completion_result(
            task_name="DoneTask",
            status=AssignmentCompletionStatus.ALREADY_DONE,
            points=0,
        )

        with (
            patch(
                "apps.bots.telegram.handlers.messages.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.messages.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.messages.handle_add_reminder_wizard",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "apps.bots.telegram.handlers.messages.handle_edit_reminder_wizard",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "apps.bots.telegram.handlers.messages.handle_delete_reminder_wizard",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch("apps.bots.telegram.handlers.messages.get_today", return_value=date(2026, 3, 15)),
            patch("apps.bots.telegram.handlers.messages.mark_assignment_done", return_value=result),
            patch(
                "apps.bots.telegram.handlers.messages.assignment_already_done",
                return_value="Already done",
            ),
        ):
            await on_message(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once_with("Already done")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_success_replaces_assignment_list(self, mock_update, mock_context):
        user = _make_user()
        mock_update.message.text = "MyTask"
        result = _make_completion_result(status=AssignmentCompletionStatus.OK)

        sent_message = MagicMock()
        sent_message.message_id = 999

        with (
            patch(
                "apps.bots.telegram.handlers.messages.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.messages.get_users", return_value=[user]),
            patch(
                "apps.bots.telegram.handlers.messages.handle_add_reminder_wizard",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "apps.bots.telegram.handlers.messages.handle_edit_reminder_wizard",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "apps.bots.telegram.handlers.messages.handle_delete_reminder_wizard",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch("apps.bots.telegram.handlers.messages.get_today", return_value=date(2026, 3, 15)),
            patch("apps.bots.telegram.handlers.messages.mark_assignment_done", return_value=result),
            patch(
                "apps.bots.telegram.handlers.messages.build_assignment_list",
                return_value=("Updated list", None),
            ),
        ):
            mock_context.bot.send_message.return_value = sent_message
            await on_message(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        assert mock_context.user_data["assignments_message_id"] == 999


class TestOnAssignmentButton:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_user_not_registered_shows_error(self, mock_update, mock_context):
        query = MagicMock()
        query.from_user.id = 123456
        query.data = "assignment_1|TaskName"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        mock_update.callback_query = query

        with (
            patch(
                "apps.bots.telegram.handlers.messages.get_active_user_by_telegram_chat_id",
                return_value=None,
            ),
            patch("apps.bots.telegram.handlers.messages.get_users", return_value=[_make_user()]),
            patch(
                "apps.bots.telegram.handlers.messages.telegram_chat_id_not_registered",
                return_value="Not registered",
            ),
        ):
            await on_assignment_button(mock_update, mock_context)

        query.answer.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_task_not_found_shows_error(self, mock_update, mock_context):
        user = _make_user()
        query = MagicMock()
        query.from_user.id = 123456
        query.data = "assignment_1|TaskName"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        mock_update.callback_query = query
        result = _make_completion_result(status=AssignmentCompletionStatus.NOT_FOUND, points=0)

        with (
            patch(
                "apps.bots.telegram.handlers.messages.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.messages.get_today", return_value=date(2026, 3, 15)),
            patch("apps.bots.telegram.handlers.messages.mark_assignment_done", return_value=result),
            patch(
                "apps.bots.telegram.handlers.messages.assignment_not_found",
                return_value="Not found",
            ),
        ):
            await on_assignment_button(mock_update, mock_context)

        query.answer.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_already_done_shows_alert(self, mock_update, mock_context):
        user = _make_user()
        query = MagicMock()
        query.from_user.id = 123456
        query.data = "assignment_1|TaskName"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        mock_update.callback_query = query
        result = _make_completion_result(
            task_name="TaskName",
            status=AssignmentCompletionStatus.ALREADY_DONE,
            points=0,
        )

        with (
            patch(
                "apps.bots.telegram.handlers.messages.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.messages.get_today", return_value=date(2026, 3, 15)),
            patch("apps.bots.telegram.handlers.messages.mark_assignment_done", return_value=result),
            patch(
                "apps.bots.telegram.handlers.messages.assignment_already_done",
                return_value="Already done",
            ),
            patch(
                "apps.bots.telegram.handlers.messages.build_assignment_list",
                return_value=("List text", None),
            ),
        ):
            await on_assignment_button(mock_update, mock_context)

        query.answer.assert_called_once_with("Already done")
        query.edit_message_text.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_success_updates_message(self, mock_update, mock_context):
        user = _make_user()
        query = MagicMock()
        query.from_user.id = 123456
        query.data = "assignment_1|TaskName"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        mock_update.callback_query = query
        result = _make_completion_result(status=AssignmentCompletionStatus.OK)

        with (
            patch(
                "apps.bots.telegram.handlers.messages.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.messages.get_today", return_value=date(2026, 3, 15)),
            patch("apps.bots.telegram.handlers.messages.mark_assignment_done", return_value=result),
            patch(
                "apps.bots.telegram.handlers.messages.build_assignment_list",
                return_value=("Updated list", None),
            ),
        ):
            await on_assignment_button(mock_update, mock_context)

        query.answer.assert_called_once_with(None)
        query.edit_message_text.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unregistered_user_edit_ignores_bad_request(self, mock_update, mock_context):
        query = MagicMock()
        query.from_user.id = 123456
        query.data = "assignment_1|TaskName"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock(side_effect=BadRequest("message is not modified"))
        mock_update.callback_query = query

        with (
            patch(
                "apps.bots.telegram.handlers.messages.get_active_user_by_telegram_chat_id",
                return_value=None,
            ),
            patch("apps.bots.telegram.handlers.messages.get_users", return_value=[_make_user()]),
            patch(
                "apps.bots.telegram.handlers.messages.telegram_chat_id_not_registered",
                return_value="Not registered",
            ),
        ):
            await on_assignment_button(mock_update, mock_context)

        query.edit_message_text.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_task_not_found_edit_ignores_bad_request(self, mock_update, mock_context):
        user = _make_user()
        query = MagicMock()
        query.from_user.id = 123456
        query.data = "assignment_1|TaskName"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock(side_effect=BadRequest("message is not modified"))
        mock_update.callback_query = query
        result = _make_completion_result(status=AssignmentCompletionStatus.NOT_FOUND, points=0)

        with (
            patch(
                "apps.bots.telegram.handlers.messages.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.messages.get_today", return_value=date(2026, 3, 15)),
            patch("apps.bots.telegram.handlers.messages.mark_assignment_done", return_value=result),
            patch(
                "apps.bots.telegram.handlers.messages.assignment_not_found",
                return_value="Not found",
            ),
        ):
            await on_assignment_button(mock_update, mock_context)

        query.edit_message_text.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_success_edit_ignores_bad_request(self, mock_update, mock_context):
        user = _make_user()
        query = MagicMock()
        query.from_user.id = 123456
        query.data = "assignment_1|TaskName"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock(side_effect=BadRequest("message is not modified"))
        mock_update.callback_query = query
        result = _make_completion_result(status=AssignmentCompletionStatus.OK)

        with (
            patch(
                "apps.bots.telegram.handlers.messages.get_active_user_by_telegram_chat_id",
                return_value=user,
            ),
            patch("apps.bots.telegram.handlers.messages.get_today", return_value=date(2026, 3, 15)),
            patch("apps.bots.telegram.handlers.messages.mark_assignment_done", return_value=result),
            patch(
                "apps.bots.telegram.handlers.messages.build_assignment_list",
                return_value=("Updated list", None),
            ),
        ):
            await on_assignment_button(mock_update, mock_context)

        query.edit_message_text.assert_called_once()


class TestBuildAssignmentList:
    @pytest.mark.unit
    def test_builds_list_with_pending_and_completed(self):
        user = _make_user()
        today = date(2026, 3, 15)
        assignments = [_make_assignment(task_id=1, task_name="Task1")]
        pending = [_make_assignment(task_id=1, task_name="Task1")]

        with (
            patch(
                "apps.bots.telegram.handlers.messages.get_daily_assignments",
                return_value=assignments,
            ),
            patch(
                "apps.bots.telegram.handlers.messages.get_pending_daily_assignments",
                return_value=pending,
            ),
            patch(
                "apps.bots.telegram.handlers.messages.assignments_list",
                return_value="Assignments text",
            ),
        ):
            text, markup = build_assignment_list(user, today)

        assert text == "Assignments text"
        assert markup is not None

    @pytest.mark.unit
    def test_all_completed_returns_no_keyboard(self):
        user = _make_user()
        today = date(2026, 3, 15)
        assignments = [_make_assignment(task_id=1, task_name="Task1")]
        pending = []

        with (
            patch(
                "apps.bots.telegram.handlers.messages.get_daily_assignments",
                return_value=assignments,
            ),
            patch(
                "apps.bots.telegram.handlers.messages.get_pending_daily_assignments",
                return_value=pending,
            ),
            patch(
                "apps.bots.telegram.handlers.messages.assignments_list",
                return_value="Assignments text",
            ),
        ):
            text, markup = build_assignment_list(user, today)

        assert text == "Assignments text"
        assert markup is None


class TestAnswerQuery:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_answer_query_bad_request_ignored(self):
        query = MagicMock()
        query.answer = AsyncMock(side_effect=BadRequest("query is too old"))

        await answer_query(query, "test")

        query.answer.assert_called_once_with("test")


class TestReplaceAssignmentList:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_bad_request_ignored(self, mock_context):
        user = _make_user()
        mock_context.user_data["assignments_message_id"] = 888
        mock_context.bot.delete_message.side_effect = BadRequest("message to delete not found")
        mock_context.bot.send_message.return_value = MagicMock(message_id=100)

        with (
            patch(
                "apps.bots.telegram.handlers.messages.get_daily_assignments",
                return_value=[],
            ),
            patch(
                "apps.bots.telegram.handlers.messages.get_pending_daily_assignments",
                return_value=[],
            ),
            patch(
                "apps.bots.telegram.handlers.messages.assignments_list",
                return_value="Assignments text",
            ),
        ):
            await replace_assignment_list("123456", user, date(2026, 3, 15), mock_context)

        mock_context.bot.delete_message.assert_called_once()
        mock_context.bot.send_message.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_with_prefix(self, mock_context):
        user = _make_user()
        mock_context.bot.send_message.return_value = MagicMock(message_id=100)

        with (
            patch(
                "apps.bots.telegram.handlers.messages.get_daily_assignments",
                return_value=[],
            ),
            patch(
                "apps.bots.telegram.handlers.messages.get_pending_daily_assignments",
                return_value=[],
            ),
            patch(
                "apps.bots.telegram.handlers.messages.assignments_list",
                return_value="Assignments text",
            ),
        ):
            await replace_assignment_list(
                "123456", user, date(2026, 3, 15), mock_context, prefix="Done!"
            )

        call_args = mock_context.bot.send_message.call_args
        assert "Done!" in call_args.kwargs["text"]
