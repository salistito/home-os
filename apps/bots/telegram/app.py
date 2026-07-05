from datetime import time
from zoneinfo import ZoneInfo

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from apps.bots.telegram.handlers.commands import on_balance_command, on_tasks_command
from apps.bots.telegram.handlers.messages import on_message, on_task_button, start
from apps.bots.telegram.jobs import send_daily_assignments
from core.config import TELEGRAM_BOT_TOKEN, TZ


def build_app() -> Application:
    tz = ZoneInfo(TZ)
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", on_balance_command))
    app.add_handler(CommandHandler("tasks", on_tasks_command))
    app.add_handler(CallbackQueryHandler(on_task_button, pattern=r"^task_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    app.job_queue.run_daily(
        send_daily_assignments,
        time=time(hour=8, minute=0, tzinfo=tz),
    )
    return app
