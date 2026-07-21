import random
import sqlite3

from core.db import get_connection
from modules.finances.errors import OpenPeriodExistsError
from modules.finances.types import Entry, EntryDetail, Period, Tag

TAG_COLORS = (
    "rose",
    "fuchsia",
    "violet",
    "sky",
    "teal",
    "green",
    "yellow",
    "slate",
)

_PERIOD_COLUMNS = "id, label, status, opened_at"
_ENTRY_COLUMNS = (
    "id, period_id, kind, scope, owner_id, label, amount, status, paid_at, detail_mode, created_at"
)
_DETAIL_COLUMNS = "id, entry_id, label, amount"
_TAG_COLUMNS = "id, name, color, created_at"


def _row_to_period(row) -> Period:
    return Period(
        row["id"],
        row["label"],
        row["status"],
        row["opened_at"],
    )


def _row_to_entry(row) -> Entry:
    return Entry(
        row["id"],
        row["period_id"],
        row["kind"],
        row["scope"],
        row["owner_id"],
        row["label"],
        row["amount"],
        row["status"],
        row["paid_at"],
        row["detail_mode"],
        row["created_at"],
    )


def _row_to_detail(row) -> EntryDetail:
    return EntryDetail(row["id"], row["entry_id"], row["label"], row["amount"])


def _row_to_tag(row) -> Tag:
    return Tag(row["id"], row["name"], row["color"], row["created_at"])


def _tags_for(conn, entry_ids: list[int]) -> dict[int, list[Tag]]:
    if not entry_ids:
        return {}
    placeholders = ",".join("?" * len(entry_ids))
    rows = conn.execute(
        f"""
        SELECT et.entry_id AS entry_id, {", ".join(f"t.{c}" for c in _TAG_COLUMNS.split(", "))}
        FROM finances_entry_tags et
        JOIN finances_tags t ON t.id = et.tag_id
        WHERE et.entry_id IN ({placeholders})
        ORDER BY t.name COLLATE NOCASE
        """,
        entry_ids,
    ).fetchall()
    grouped: dict[int, list[Tag]] = {}
    for row in rows:
        grouped.setdefault(row["entry_id"], []).append(_row_to_tag(row))
    return grouped


def _details_for(conn, entry_ids: list[int]) -> dict[int, list[EntryDetail]]:
    if not entry_ids:
        return {}
    placeholders = ",".join("?" * len(entry_ids))
    rows = conn.execute(
        f"SELECT {_DETAIL_COLUMNS} FROM finances_entry_details "
        f"WHERE entry_id IN ({placeholders}) ORDER BY id",
        entry_ids,
    ).fetchall()
    grouped: dict[int, list[EntryDetail]] = {}
    for row in rows:
        grouped.setdefault(row["entry_id"], []).append(_row_to_detail(row))
    return grouped


def create_period(label: str, opened_at: str) -> Period:
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO finances_periods (label, status, opened_at)
                VALUES (?, 'open', ?)
                """,
                (label, opened_at),
            )
        return get_period_by_id(cur.lastrowid)

    except sqlite3.IntegrityError as e:
        open_period = get_open_period()
        raise OpenPeriodExistsError(open_period) from e


def close_open_period() -> None:
    with get_connection() as conn:
        conn.execute("UPDATE finances_periods SET status = 'closed' WHERE status = 'open'")


def get_open_period() -> Period | None:
    with get_connection() as conn:
        row = conn.execute(
            f"SELECT {_PERIOD_COLUMNS} FROM finances_periods WHERE status = 'open'"
        ).fetchone()
    return _row_to_period(row) if row else None


def get_period_by_id(period_id: int) -> Period | None:
    with get_connection() as conn:
        row = conn.execute(
            f"SELECT {_PERIOD_COLUMNS} FROM finances_periods WHERE id = ?",
            (period_id,),
        ).fetchone()
    return _row_to_period(row) if row else None


def get_period_by_label(label: str) -> Period | None:
    with get_connection() as conn:
        row = conn.execute(
            f"SELECT {_PERIOD_COLUMNS} FROM finances_periods WHERE label = ?",
            (label,),
        ).fetchone()
    return _row_to_period(row) if row else None


def get_periods() -> list[Period]:
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT {_PERIOD_COLUMNS} FROM finances_periods ORDER BY id DESC"
        ).fetchall()
    return [_row_to_period(r) for r in rows]


def create_entry(
    period_id: int,
    kind: str,
    scope: str,
    owner_id: int,
    label: str,
    amount: int | None,
    created_at: str,
) -> Entry:
    pending = amount is None
    status = "pending" if pending else "confirmed"
    paid_at = None if pending else created_at
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO finances_entries
                (period_id, kind, scope, owner_id, label, amount,
                 status, paid_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (period_id, kind, scope, owner_id, label, amount, status, paid_at, created_at),
        )
    return get_entry_by_id(cur.lastrowid)


def update_entry(
    entry_id: int, label: str, owner_id: int, amount: int, detail_mode: str
) -> Entry | None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE finances_entries
            SET label = ?, owner_id = ?, amount = ?, detail_mode = ?
            WHERE id = ?
            """,
            (label, owner_id, amount, detail_mode, entry_id),
        )
    return get_entry_by_id(entry_id)


def replace_entry_details(entry_id: int, details: list[tuple[str, int]]) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM finances_entry_details WHERE entry_id = ?", (entry_id,))
        conn.executemany(
            "INSERT INTO finances_entry_details (entry_id, label, amount) VALUES (?, ?, ?)",
            [(entry_id, label, amount) for label, amount in details],
        )


def clone_confirmed_entries(from_period_id: int, to_period_id: int, created_at: str) -> None:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_ENTRY_COLUMNS}
            FROM finances_entries
            WHERE period_id = ? AND status = 'confirmed'
            ORDER BY id
            """,
            (from_period_id,),
        ).fetchall()
        for row in rows:
            cur = conn.execute(
                """
                INSERT INTO finances_entries
                    (period_id, kind, scope, owner_id, label, amount,
                     status, paid_at, detail_mode, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'pending', NULL, ?, ?)
                """,
                (
                    to_period_id,
                    row["kind"],
                    row["scope"],
                    row["owner_id"],
                    row["label"],
                    row["amount"],
                    row["detail_mode"],
                    created_at,
                ),
            )
            details = conn.execute(
                f"SELECT {_DETAIL_COLUMNS} FROM finances_entry_details "
                "WHERE entry_id = ? ORDER BY id",
                (row["id"],),
            ).fetchall()
            conn.executemany(
                "INSERT INTO finances_entry_details (entry_id, label, amount) VALUES (?, ?, ?)",
                [(cur.lastrowid, d["label"], d["amount"]) for d in details],
            )
            tag_rows = conn.execute(
                "SELECT tag_id FROM finances_entry_tags WHERE entry_id = ?",
                (row["id"],),
            ).fetchall()
            conn.executemany(
                "INSERT INTO finances_entry_tags (entry_id, tag_id) VALUES (?, ?)",
                [(cur.lastrowid, t["tag_id"]) for t in tag_rows],
            )


def set_entry_status(entry_id: int, status: str, paid_at: str | None) -> Entry | None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE finances_entries SET status = ?, paid_at = ? WHERE id = ?",
            (status, paid_at, entry_id),
        )
    return get_entry_by_id(entry_id)


def delete_entry(entry_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM finances_entries WHERE id = ?", (entry_id,))


def get_entry_by_id(entry_id: int) -> Entry | None:
    with get_connection() as conn:
        row = conn.execute(
            f"SELECT {_ENTRY_COLUMNS} FROM finances_entries WHERE id = ?",
            (entry_id,),
        ).fetchone()
        if row is None:
            return None
        entry = _row_to_entry(row)
        entry.details = _details_for(conn, [entry.id]).get(entry.id, [])
        entry.tags = _tags_for(conn, [entry.id]).get(entry.id, [])
    return entry


def get_entries_by_period(period_id: int) -> list[Entry]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_ENTRY_COLUMNS}
            FROM finances_entries
            WHERE period_id = ?
            ORDER BY id
            """,
            (period_id,),
        ).fetchall()
        entries = [_row_to_entry(r) for r in rows]
        entry_ids = [e.id for e in entries]
        details = _details_for(conn, entry_ids)
        tags = _tags_for(conn, entry_ids)
        for entry in entries:
            entry.details = details.get(entry.id, [])
            entry.tags = tags.get(entry.id, [])
    return entries


def get_tags() -> list[Tag]:
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT {_TAG_COLUMNS} FROM finances_tags ORDER BY name COLLATE NOCASE"
        ).fetchall()
    return [_row_to_tag(r) for r in rows]


def get_or_create_tag_ids(names: list[str], created_at: str) -> list[int]:
    ids: list[int] = []
    with get_connection() as conn:
        for name in names:
            row = conn.execute(
                "SELECT id FROM finances_tags WHERE name = ? COLLATE NOCASE",
                (name,),
            ).fetchone()
            if row is not None:
                ids.append(row["id"])
                continue
            cur = conn.execute(
                "INSERT INTO finances_tags (name, color, created_at) VALUES (?, ?, ?)",
                (name, random.choice(TAG_COLORS), created_at),
            )
            ids.append(cur.lastrowid)
    return ids


def set_entry_tags(entry_id: int, tag_ids: list[int]) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM finances_entry_tags WHERE entry_id = ?", (entry_id,))
        conn.executemany(
            "INSERT INTO finances_entry_tags (entry_id, tag_id) VALUES (?, ?)",
            [(entry_id, tag_id) for tag_id in tag_ids],
        )
