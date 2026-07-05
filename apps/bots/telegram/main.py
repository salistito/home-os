from apps.bots.telegram.app import build_app
from core.config import TELEGRAM_BOT_TOKEN
from core.db import init_db
from core.seed import load_seed


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN no configurado")
    init_db()
    load_seed()
    app = build_app()
    app.run_polling()


if __name__ == "__main__":
    main()
