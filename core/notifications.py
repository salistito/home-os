import json
import urllib.error
import urllib.request

from core.config import TELEGRAM_BOT_TOKEN


def notify(chat_id: str, message: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": message}).encode()
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        raise RuntimeError(f"Telegram sendMessage failed: {body}") from exc
