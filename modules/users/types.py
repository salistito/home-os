from dataclasses import dataclass


@dataclass
class User:
    id: str
    name: str
    telegram_chat_id: str
    password_hash: str | None
