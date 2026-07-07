from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from apps.bots.telegram.handlers.commands import (
    on_assignments_command,
    on_balance_command,
    on_help_command,
    on_start_command,
)
from apps.bots.telegram.handlers.messages import on_message, on_assignment_button
from core.config import TELEGRAM_BOT_TOKEN


def build_app() -> Application:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", on_start_command))
    app.add_handler(CommandHandler("help", on_help_command))
    app.add_handler(CommandHandler("assignments", on_assignments_command))
    app.add_handler(CommandHandler("balance", on_balance_command))
    app.add_handler(CallbackQueryHandler(on_assignment_button, pattern=r"^assignment_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    return app
