import asyncio
import logging

from telegram import Bot

from apps.bots.telegram.jobs import send_daily_assignments
from core.config import TELEGRAM_BOT_TOKEN
from core.db import init_db
from core.seed import load_seed

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        level=logging.INFO,
    )
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN no configurado")

    init_db()
    load_seed()
    await send_daily_assignments(Bot(token=TELEGRAM_BOT_TOKEN))
    logger.info("Asignaciones diarias completadas")


if __name__ == "__main__":
    asyncio.run(main())
