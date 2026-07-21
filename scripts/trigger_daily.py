import asyncio
import logging

from telegram import Bot

from apps.bots.telegram.jobs import send_daily_assignments, send_day_reminders
from core.config import TELEGRAM_BOT_TOKEN
from core.db import init_db

logger = logging.getLogger(__name__)


# This file runs locally to send daily assignments and day reminders.
async def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        level=logging.INFO,
    )
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN no configurado")

    init_db()
    await send_daily_assignments(Bot(token=TELEGRAM_BOT_TOKEN))
    await send_day_reminders(Bot(token=TELEGRAM_BOT_TOKEN))
    logger.info("Daily assignments and day reminders sent")


if __name__ == "__main__":
    asyncio.run(main())
