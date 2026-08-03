_TAG_PALETTE = (
    "fuchsia",
    "violet",
    "indigo",
    "sky",
    "teal",
    "lime",
    "orange",
)


def _color_for_name(name: str) -> str:
    hash_value = 0
    for ch in name:
        hash_value = ((hash_value << 5) - hash_value + ord(ch)) & 0xFFFFFFFF
    if hash_value >= 0x80000000:
        hash_value -= 0x100000000
    return _TAG_PALETTE[abs(hash_value) % len(_TAG_PALETTE)]


def migrate(conn):
    rows = conn.execute(
        "SELECT id, name, color FROM finances_tags"
    ).fetchall()
    for tag_id, name, color in rows:
        if color in _TAG_PALETTE:
            continue
        conn.execute(
            "UPDATE finances_tags SET color = ? WHERE id = ?",
            (_color_for_name(name), tag_id),
        )
