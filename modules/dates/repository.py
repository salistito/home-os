import sqlite3

from core.db import get_connection
from modules.dates.errors import EventAlreadyExistsError
from modules.dates.types import (
    DateAttribute,
    DateCouple,
    DateEvent,
    DateMemory,
    DateMilestone,
)

_COUPLE_COLUMNS = "id, started_at, relationship_status, status, created_at, updated_at"
_MEMBER_COLUMNS = "id, couple_id, user_id"
_EVENT_COLUMNS = (
    "id, couple_id, week_start, planned_by, scheduled_date, scheduled_time, "
    "title, status, created_at, updated_at"
)
_ATTRIBUTE_COLUMNS = "id, event_id, key, value, is_secret, reveal_on"
_MEMORY_COLUMNS = "id, event_id, kind, media_url, caption, taken_by, created_at"
_MILESTONE_COLUMNS = "id, couple_id, type, date, label, notes, created_at"

EDITABLE_EVENT_COLUMNS = {
    "planned_by",
    "scheduled_date",
    "scheduled_time",
    "title",
    "status",
}


def _row_to_couple(row) -> DateCouple:
    return DateCouple(
        id=row["id"],
        member_ids=[],
        started_at=row["started_at"],
        relationship_status=row["relationship_status"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_event(row) -> DateEvent:
    return DateEvent(
        id=row["id"],
        couple_id=row["couple_id"],
        week_start=row["week_start"],
        planned_by=row["planned_by"],
        scheduled_date=row["scheduled_date"],
        scheduled_time=row["scheduled_time"],
        title=row["title"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_attribute(row) -> DateAttribute:
    return DateAttribute(
        id=row["id"],
        event_id=row["event_id"],
        key=row["key"],
        value=row["value"],
        is_secret=bool(row["is_secret"]),
        reveal_on=row["reveal_on"],
    )


def _row_to_memory(row) -> DateMemory:
    return DateMemory(
        id=row["id"],
        event_id=row["event_id"],
        kind=row["kind"],
        media_url=row["media_url"],
        caption=row["caption"],
        taken_by=row["taken_by"],
        created_at=row["created_at"],
    )


# Couples


def get_couple_by_id(couple_id: int) -> DateCouple | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_COUPLE_COLUMNS}
            FROM date_couples
            WHERE id = ?
            """,
            (couple_id,),
        ).fetchone()
    if row is None:
        return None
    couple = _row_to_couple(row)
    couple.member_ids = get_couple_member_ids(couple_id)
    return couple


def get_couples(status: str | None = "active") -> list[DateCouple]:
    where = ""
    params: tuple = ()
    if status is not None:
        where = "WHERE status = ?"
        params = (status,)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_COUPLE_COLUMNS}
            FROM date_couples
            {where}
            ORDER BY id
            """,
            params,
        ).fetchall()
    couples = [_row_to_couple(r) for r in rows]
    member_rows = _get_all_member_rows()
    by_couple: dict[int, list[int]] = {}
    for member_row in member_rows:
        by_couple.setdefault(member_row["couple_id"], []).append(member_row["user_id"])
    for couple in couples:
        couple.member_ids = by_couple.get(couple.id, [])
    return couples


def create_couple(
    created_at: str,
    updated_at: str,
    started_at: str | None = None,
    relationship_status: str = "couple",
) -> DateCouple:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO date_couples
                (started_at, relationship_status, status, created_at, updated_at)
            VALUES (?, ?, 'active', ?, ?)
            """,
            (started_at, relationship_status, created_at, updated_at),
        )
    return get_couple_by_id(cur.lastrowid)


def update_couple(
    couple_id: int,
    updated_at: str,
    started_at: str | None = None,
    relationship_status: str | None = None,
    status: str | None = None,
) -> bool:
    set_clauses = ["updated_at = ?"]
    params: list[str | None] = [updated_at]
    if started_at is not None:
        set_clauses.append("started_at = ?")
        params.append(started_at)
    if relationship_status is not None:
        set_clauses.append("relationship_status = ?")
        params.append(relationship_status)
    if status is not None:
        set_clauses.append("status = ?")
        params.append(status)
    params.append(couple_id)
    with get_connection() as conn:
        cur = conn.execute(
            f"""
            UPDATE date_couples
            SET {", ".join(set_clauses)}
            WHERE id = ?
            """,
            params,
        )
    return cur.rowcount > 0


def delete_couple(couple_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            DELETE FROM date_couples
            WHERE id = ?
            """,
            (couple_id,),
        )
    return cur.rowcount > 0


def get_couple_member_ids(couple_id: int) -> list[int]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_MEMBER_COLUMNS}
            FROM date_couple_members
            WHERE couple_id = ?
            ORDER BY id
            """,
            (couple_id,),
        ).fetchall()
    return [row["user_id"] for row in rows]


def _get_all_member_rows() -> list:
    with get_connection() as conn:
        return conn.execute(
            f"""
            SELECT {_MEMBER_COLUMNS}
            FROM date_couple_members
            ORDER BY couple_id, id
            """
        ).fetchall()


def replace_couple_members(couple_id: int, member_ids: list[int]) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM date_couple_members
            WHERE couple_id = ?
            """,
            (couple_id,),
        )
        conn.executemany(
            """
            INSERT INTO date_couple_members (couple_id, user_id)
            VALUES (?, ?)
            """,
            [(couple_id, member_id) for member_id in member_ids],
        )


# Events


def get_event_by_id(event_id: int) -> DateEvent | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_EVENT_COLUMNS}
            FROM date_events
            WHERE id = ?
            """,
            (event_id,),
        ).fetchone()
    if row is None:
        return None
    event = _row_to_event(row)
    event.attributes = get_event_attributes(event_id)
    return event


def create_event(
    couple_id: int,
    week_start: str,
    planned_by: int,
    created_at: str,
    updated_at: str,
    scheduled_date: str | None = None,
    scheduled_time: str | None = None,
    title: str | None = None,
) -> DateEvent:
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO date_events
                    (couple_id, week_start, planned_by, scheduled_date,
                     scheduled_time, title, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'planned', ?, ?)
                """,
                (
                    couple_id,
                    week_start,
                    planned_by,
                    scheduled_date,
                    scheduled_time,
                    title,
                    created_at,
                    updated_at,
                ),
            )
        return get_event_by_id(cur.lastrowid)

    except sqlite3.IntegrityError as e:
        raise EventAlreadyExistsError(couple_id, week_start) from e


def update_event(event_id: int, updated_at: str, **fields: str | None) -> bool:
    if not fields:
        return True

    invalid = set(fields) - EDITABLE_EVENT_COLUMNS
    if invalid:
        raise ValueError(f"Invalid editable date event columns: {', '.join(sorted(invalid))}")

    set_clauses: list[str] = []
    params: list[str | None] = []
    for column, value in fields.items():
        if value is None:
            set_clauses.append(f"{column} = NULL")
        else:
            set_clauses.append(f"{column} = ?")
            params.append(value)
    set_clauses.append("updated_at = ?")
    params.append(updated_at)
    params.append(event_id)

    with get_connection() as conn:
        cur = conn.execute(
            f"""
            UPDATE date_events
            SET {", ".join(set_clauses)}
            WHERE id = ?
            """,
            params,
        )
    return cur.rowcount > 0


def delete_event(event_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            DELETE FROM date_events
            WHERE id = ?
            """,
            (event_id,),
        )
    return cur.rowcount > 0


def list_events(
    couple_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[DateEvent]:
    clauses: list[str] = []
    params: list[str | int] = []
    if couple_id is not None:
        clauses.append("couple_id = ?")
        params.append(couple_id)
    if from_date is not None:
        clauses.append("week_start >= ?")
        params.append(from_date)
    if to_date is not None:
        clauses.append("week_start <= ?")
        params.append(to_date)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_EVENT_COLUMNS}
            FROM date_events
            {where}
            ORDER BY week_start
            """,
            params,
        ).fetchall()
    events = [_row_to_event(r) for r in rows]
    attribute_rows = _get_all_attribute_rows()
    by_event: dict[int, list[DateAttribute]] = {}
    for attr_row in attribute_rows:
        attr = _row_to_attribute(attr_row)
        by_event.setdefault(attr.event_id, []).append(attr)
    for event in events:
        event.attributes = by_event.get(event.id, [])
    return events


def get_last_event(couple_id: int) -> DateEvent | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_EVENT_COLUMNS}
            FROM date_events
            WHERE couple_id = ?
            ORDER BY week_start DESC
            LIMIT 1
            """,
            (couple_id,),
        ).fetchone()
    if row is None:
        return None
    event = _row_to_event(row)
    event.attributes = get_event_attributes(event_id=event.id)
    return event


# Attributes


def _get_all_attribute_rows() -> list:
    with get_connection() as conn:
        return conn.execute(
            f"""
            SELECT {_ATTRIBUTE_COLUMNS}
            FROM date_attributes
            ORDER BY id
            """
        ).fetchall()


def get_event_attributes(event_id: int) -> list[DateAttribute]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_ATTRIBUTE_COLUMNS}
            FROM date_attributes
            WHERE event_id = ?
            ORDER BY id
            """,
            (event_id,),
        ).fetchall()
    return [_row_to_attribute(r) for r in rows]


def replace_event_attributes(
    event_id: int, attributes: list[tuple[str, str, bool, str | None]]
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM date_attributes
            WHERE event_id = ?
            """,
            (event_id,),
        )
        conn.executemany(
            """
            INSERT INTO date_attributes (event_id, key, value, is_secret, reveal_on)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (event_id, key, value, int(is_secret), reveal_on)
                for key, value, is_secret, reveal_on in attributes
            ],
        )


def get_attribute_by_id(attribute_id: int) -> DateAttribute | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_ATTRIBUTE_COLUMNS}
            FROM date_attributes
            WHERE id = ?
            """,
            (attribute_id,),
        ).fetchone()
    return _row_to_attribute(row) if row else None


# Memories


def get_memory_by_id(memory_id: int) -> DateMemory | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_MEMORY_COLUMNS}
            FROM date_memories
            WHERE id = ?
            """,
            (memory_id,),
        ).fetchone()
    return _row_to_memory(row) if row else None


def create_memory(
    event_id: int,
    kind: str,
    created_at: str,
    media_url: str | None = None,
    caption: str | None = None,
    taken_by: int | None = None,
) -> DateMemory:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO date_memories (event_id, kind, media_url, caption, taken_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (event_id, kind, media_url, caption, taken_by, created_at),
        )
    return get_memory_by_id(cur.lastrowid)


def list_memories(event_id: int) -> list[DateMemory]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_MEMORY_COLUMNS}
            FROM date_memories
            WHERE event_id = ?
            ORDER BY id
            """,
            (event_id,),
        ).fetchall()
    return [_row_to_memory(r) for r in rows]


def delete_memory(memory_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            DELETE FROM date_memories
            WHERE id = ?
            """,
            (memory_id,),
        )
    return cur.rowcount > 0


# Milestones


def _row_to_milestone(row) -> DateMilestone:
    return DateMilestone(
        id=row["id"],
        couple_id=row["couple_id"],
        type=row["type"],
        date=row["date"],
        label=row["label"],
        notes=row["notes"],
        created_at=row["created_at"],
    )


def get_milestone_by_id(milestone_id: int) -> DateMilestone | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_MILESTONE_COLUMNS}
            FROM date_couple_milestones
            WHERE id = ?
            """,
            (milestone_id,),
        ).fetchone()
    return _row_to_milestone(row) if row else None


def create_milestone(
    couple_id: int,
    milestone_type: str,
    date: str,
    label: str,
    created_at: str,
    notes: str | None = None,
) -> DateMilestone:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO date_couple_milestones (couple_id, type, date, label, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (couple_id, milestone_type, date, label, notes, created_at),
        )
    return get_milestone_by_id(cur.lastrowid)


def list_milestones(couple_id: int) -> list[DateMilestone]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_MILESTONE_COLUMNS}
            FROM date_couple_milestones
            WHERE couple_id = ?
            ORDER BY id
            """,
            (couple_id,),
        ).fetchall()
    return [_row_to_milestone(r) for r in rows]


def delete_milestone(milestone_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            DELETE FROM date_couple_milestones
            WHERE id = ?
            """,
            (milestone_id,),
        )
    return cur.rowcount > 0
