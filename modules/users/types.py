from dataclasses import dataclass
from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    MEMBER = "member"


@dataclass
class User:
    id: int
    name: str
    role: str = UserRole.MEMBER
    password_hash: str | None = None
    telegram_chat_id: str | None = None
    deleted_at: str | None = None
