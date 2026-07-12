import bcrypt


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    return bcrypt.checkpw(plain.encode("utf-8"), password_hash.encode("utf-8"))
