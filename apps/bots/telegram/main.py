import asyncio
import logging
from http import HTTPStatus

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from telegram import Update

from apps.bots.telegram.app import build_app
from apps.bots.telegram.jobs import send_daily_assignments
from core.config import PORT, TELEGRAM_BOT_TOKEN, WEBHOOK_SECRET, WEBHOOK_URL
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
    if not (WEBHOOK_URL and WEBHOOK_SECRET):
        raise SystemExit("WEBHOOK_URL y WEBHOOK_SECRET son obligatorios")

    init_db()
    load_seed()
    application = build_app()

    async def telegram(request: Request) -> Response:
        if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
            return Response(status_code=HTTPStatus.FORBIDDEN)
        update = Update.de_json(await request.json(), application.bot)
        await application.update_queue.put(update)
        return Response()

    async def trigger_daily(request: Request) -> Response:
        if request.path_params["token"] != WEBHOOK_SECRET:
            return Response(status_code=HTTPStatus.FORBIDDEN)
        await send_daily_assignments(application.bot)
        return PlainTextResponse("ok")

    starlette_app = Starlette(
        routes=[
            Route("/telegram", telegram, methods=["POST"]),
            Route("/trigger-daily/{token}", trigger_daily, methods=["GET", "POST"]),
        ]
    )
    webserver = uvicorn.Server(
        config=uvicorn.Config(app=starlette_app, host="0.0.0.0", port=PORT)
    )

    async with application:
        await application.bot.set_webhook(
            url=f"{WEBHOOK_URL.rstrip('/')}/telegram",
            secret_token=WEBHOOK_SECRET,
            allowed_updates=Update.ALL_TYPES,
        )
        await application.start()
        logger.info("Bot iniciado en modo webhook en el puerto %s", PORT)
        await webserver.serve()
        await application.stop()


if __name__ == "__main__":
    asyncio.run(main())