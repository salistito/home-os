import logging

from apps.bots.telegram.app import build_app
from core.config import PORT, TELEGRAM_BOT_TOKEN, WEBHOOK_SECRET, WEBHOOK_URL
from core.db import init_db
from core.seed import load_seed

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        level=logging.INFO,
    )
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN no configurado")
    init_db()
    load_seed()
    app = build_app()

    if WEBHOOK_URL:
        if not WEBHOOK_SECRET:
            raise SystemExit("WEBHOOK_SECRET no configurado")
        logger.info("Iniciando en modo webhook en el puerto %s", PORT)
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=WEBHOOK_SECRET,
            secret_token=WEBHOOK_SECRET,
            webhook_url=f"{WEBHOOK_URL.rstrip('/')}/{WEBHOOK_SECRET}",
        )
    else:
        logger.info("Iniciando en modo polling")
        app.run_polling()


if __name__ == "__main__":
    main()
