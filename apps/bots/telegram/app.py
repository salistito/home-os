from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

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
from apps.bots.telegram.handlers.messages import on_message, on_assignment_button
from core.config import TELEGRAM_BOT_TOKEN


def build_app() -> Application:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", on_start_command))
    app.add_handler(CommandHandler("help", on_help_command))
    app.add_handler(CommandHandler("init_home", on_init_home_command))
    app.add_handler(CommandHandler("add_member", on_add_member_command))
    app.add_handler(CommandHandler("join", on_join_command))
    app.add_handler(CommandHandler("tasks", on_tasks_command))
    app.add_handler(CommandHandler("add_task", on_add_task_command))
    app.add_handler(CommandHandler("list_tasks", on_list_tasks_command))
    app.add_handler(CommandHandler("edit_task", on_edit_task_command))
    app.add_handler(CommandHandler("delete_task", on_delete_task_command))
    app.add_handler(CommandHandler("assignments", on_assignments_command))
    app.add_handler(CommandHandler("balance", on_balance_command))
    app.add_handler(CommandHandler("reminders", on_reminders_command))
    app.add_handler(CommandHandler("add_reminder", on_add_reminder_command))
    app.add_handler(CommandHandler("list_reminders", on_list_reminders_command))
    app.add_handler(CommandHandler("edit_reminder", on_edit_reminder_command))
    app.add_handler(CommandHandler("delete_reminder", on_delete_reminder_command))
    app.add_handler(CallbackQueryHandler(on_assignment_button, pattern=r"^assignment_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    return app
