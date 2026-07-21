import pytest
from unittest.mock import MagicMock, patch

from telegram.ext import CommandHandler


@pytest.mark.unit
class TestBuildApp:
    def test_builds_application_with_token(self, monkeypatch):
        monkeypatch.setattr("apps.bots.telegram.app.TELEGRAM_BOT_TOKEN", "test-token")
        mock_app = MagicMock()
        mock_builder = MagicMock()
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_app

        with patch("apps.bots.telegram.app.Application") as mock_app_class:
            mock_app_class.builder.return_value = mock_builder
            from apps.bots.telegram.app import build_app
            result = build_app()

        mock_builder.token.assert_called_once_with("test-token")
        mock_builder.build.assert_called_once()
        assert result is mock_app

    def test_registers_all_command_handlers(self, monkeypatch):
        monkeypatch.setattr("apps.bots.telegram.app.TELEGRAM_BOT_TOKEN", "test-token")
        mock_app = MagicMock()

        with patch("apps.bots.telegram.app.Application") as mock_app_class:
            mock_app_class.builder.return_value.token.return_value.build.return_value = mock_app
            from apps.bots.telegram.app import build_app
            build_app()

        handler_calls = mock_app.add_handler.call_args_list
        handler_types = [call[0][0].__class__.__name__ for call in handler_calls]
        command_handler_count = sum(1 for h in handler_types if h == "CommandHandler")
        assert command_handler_count == 18

    def test_registers_callback_and_message_handlers(self, monkeypatch):
        monkeypatch.setattr("apps.bots.telegram.app.TELEGRAM_BOT_TOKEN", "test-token")
        mock_app = MagicMock()

        with patch("apps.bots.telegram.app.Application") as mock_app_class:
            mock_app_class.builder.return_value.token.return_value.build.return_value = mock_app
            from apps.bots.telegram.app import build_app
            build_app()

        handler_calls = mock_app.add_handler.call_args_list
        handler_types = [call[0][0].__class__.__name__ for call in handler_calls]
        assert "CallbackQueryHandler" in handler_types
        assert "MessageHandler" in handler_types

    def test_command_handler_names_are_correct(self, monkeypatch):
        monkeypatch.setattr("apps.bots.telegram.app.TELEGRAM_BOT_TOKEN", "test-token")
        mock_app = MagicMock()

        with patch("apps.bots.telegram.app.Application") as mock_app_class:
            mock_app_class.builder.return_value.token.return_value.build.return_value = mock_app
            from apps.bots.telegram.app import build_app
            build_app()

        handler_calls = mock_app.add_handler.call_args_list
        cmd_names = set()
        for call in handler_calls:
            handler = call[0][0]
            if isinstance(handler, CommandHandler):
                cmd_names.add(next(iter(handler.commands)))

        expected = {
            "start", "help", "init_home", "add_member", "join",
            "tasks", "add_task", "list_tasks", "edit_task", "delete_task",
            "assignments", "home_assignments", "balance", "reminders",
            "add_reminder", "list_reminders", "edit_reminder", "delete_reminder",
        }
        assert cmd_names == expected
