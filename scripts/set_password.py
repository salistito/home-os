import sys
import getpass

from core.db import get_connection, init_db
from core.utils.passwords import hash_password


def _set_password(user_id: int, plain: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(plain), user_id),
        )
    return cur.rowcount > 0


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python -m scripts.set_password <user_id>")
        return 2
    user_id = sys.argv[1]

    init_db()
    with get_connection() as conn:
        exists = conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone()
    if exists is None:
        print(f"No existe un user con id '{user_id}'.")
        return 1

    plain = getpass.getpass(f"Contraseña para '{user_id}': ")
    if not plain:
        print("Contraseña vacía, cancelado.")
        return 1
    if plain != getpass.getpass("Confirmar contraseña: "):
        print("Las contraseñas no coinciden.")
        return 1

    _set_password(user_id, plain)
    print(f"Contraseña actualizada para '{user_id}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
