import asyncio
import logging
import uvicorn

from http import HTTPStatus

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route

from telegram import Update

from apps.bots.telegram.app import build_app
from apps.bots.telegram.jobs import send_daily_assignments, send_day_reminders, send_timed_reminders
from apps.web.api.main import middleware as api_middleware, routes as api_routes
from core.config import PORT, TELEGRAM_BOT_TOKEN, WEBHOOK_SECRET, WEBHOOK_URL
from core.db import init_db

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        level=logging.INFO,
    )
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN no configurado")

    init_db()
    application = build_app()

    if WEBHOOK_URL and WEBHOOK_SECRET:
        await _run_webhook(application)
    else:
        await _run_polling(application)


async def _run_webhook(application) -> None:
    async def telegram(request: Request) -> Response:
        if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
            return Response(status_code=HTTPStatus.FORBIDDEN)
        update = Update.de_json(await request.json(), application.bot)
        await application.update_queue.put(update)
        return Response()

    async def trigger_daily_assignments(request: Request) -> Response:
        if request.path_params["token"] != WEBHOOK_SECRET:
            return Response(status_code=HTTPStatus.FORBIDDEN)
        await send_daily_assignments(application.bot)
        return PlainTextResponse("ok")

    async def trigger_day_reminders(request: Request) -> Response:
        if request.path_params["token"] != WEBHOOK_SECRET:
            return Response(status_code=HTTPStatus.FORBIDDEN)
        await send_day_reminders(application.bot)
        return PlainTextResponse("ok")

    async def trigger_timed_reminders(request: Request) -> Response:
        if request.path_params["token"] != WEBHOOK_SECRET:
            return Response(status_code=HTTPStatus.FORBIDDEN)
        await send_timed_reminders(application.bot)
        return PlainTextResponse("ok")

    starlette_app = Starlette(
        routes=[
            Route("/telegram", telegram, methods=["POST"]),
            Route(
                "/trigger_daily_assignments/{token}",
                trigger_daily_assignments,
                methods=["GET", "POST"],
            ),
            Route(
                "/trigger_day_reminders/{token}",
                trigger_day_reminders,
                methods=["GET", "POST"],
            ),
            Route(
                "/trigger_timed_reminders/{token}",
                trigger_timed_reminders,
                methods=["GET", "POST"],
            ),
            *api_routes,
        ],
        middleware=api_middleware,
    )
    webserver = uvicorn.Server(config=uvicorn.Config(app=starlette_app, host="0.0.0.0", port=PORT))

    async with application:
        await application.bot.set_webhook(
            url=f"{WEBHOOK_URL.rstrip('/')}/telegram",
            secret_token=WEBHOOK_SECRET,
        )
        await application.start()
        logger.info("Bot iniciado en modo webhook en el puerto %s", PORT)
        await webserver.serve()
        await application.stop()


async def _run_polling(application) -> None:
    logger.info("Iniciando en modo polling (WEBHOOK_URL no configurado)")
    async with application:
        await application.start()
        await application.updater.start_polling()
        logger.info("Bot iniciado en modo polling. Presiona Ctrl+C para detener.")
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        finally:
            await application.updater.stop()
            await application.stop()


if __name__ == "__main__":
    asyncio.run(main())
