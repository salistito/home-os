import os
from pathlib import Path
from dotenv import load_dotenv

env_file = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_file)

# General
TZ = os.environ.get("TZ", "America/Santiago")

# Database
HOME_OS_DB_PATH = os.environ.get("HOME_OS_DB_PATH", "./homeos.db")
HOME_OS_SEED_PATH = os.environ.get("HOME_OS_SEED_PATH", "./core/seed.yaml")

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# Webhook (producción)
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
PORT = int(os.environ.get("PORT", "8080"))
