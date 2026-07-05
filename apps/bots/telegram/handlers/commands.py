from datetime import date

from telegram import Update
from telegram.ext import ContextTypes

from apps.bots.telegram.formatters import format_balance
from apps.bots.telegram.jobs import send_daily_assignments
from core.identity import get_users
from modules.tasks.service import get_month_balance


async def on_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    month = date.today().strftime("%Y-%m")
    balance_data = get_month_balance(month)
    names = {user.id: user.name for user in get_users()}
    await update.message.reply_text(format_balance(month, balance_data, names))

async def on_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_daily_assignments(context)
