import os

from pathlib import Path
from dotenv import load_dotenv

env_file = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_file)

# General
TZ = os.environ.get("TZ", "America/Santiago")

# App Name
APP_NAME = os.environ.get("APP_NAME", "home-os")

# Database
HOME_OS_DB_PATH = os.environ.get("HOME_OS_DB_PATH", "./homeos.db")

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_IDS = [
    chat_id.strip()
    for chat_id in os.environ.get("TELEGRAM_CHAT_IDS", "").split(",")
    if chat_id.strip()
]

# Webhooks (production only)
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
PORT = int(os.environ.get("PORT", "8080"))

# Authentication
JWT_SECRET = os.environ.get("JWT_SECRET", "")
JWT_TTL_DAYS = int(os.environ.get("JWT_TTL_DAYS", "365"))

# Web App
WEB_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("WEB_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
WEB_PORT = int(os.environ.get("WEB_PORT", "8000"))

# External Cron Service
CRONJOB_ORG_API_KEY = os.environ.get("CRONJOB_ORG_API_KEY", "")
