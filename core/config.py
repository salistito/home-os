import os
from pathlib import Path
from dotenv import load_dotenv

env_file = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_file)

# General
TZ = os.environ.get("TZ", "America/Santiago")

# Database
HOME_OS_DB_PATH = os.environ.get("HOME_OS_DB_PATH", "./homeos.db")

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# Webhook (production)
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
PORT = int(os.environ.get("PORT", "8080"))

# Auth
JWT_SECRET = os.environ.get("JWT_SECRET", "")
JWT_TTL_DAYS = int(os.environ.get("JWT_TTL_DAYS", "365"))

# Web CORS
WEB_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("WEB_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

# Administrative web app
WEB_PORT = int(os.environ.get("WEB_PORT", "8000"))

# cron-job.org
CRONJOB_ORG_API_KEY = os.environ.get("CRONJOB_ORG_API_KEY", "")
