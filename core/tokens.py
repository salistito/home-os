from datetime import datetime, timedelta, timezone

import jwt

from core.config import JWT_SECRET, JWT_TTL_DAYS

_ALGORITHM = "HS256"


def create_token(user_id: str) -> str:
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET no está configurado.")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(days=JWT_TTL_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=_ALGORITHM)


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[_ALGORITHM])
    except jwt.InvalidTokenError:
        return None
    return payload.get("sub")
