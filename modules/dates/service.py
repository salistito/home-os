from datetime import datetime

from core.utils.date import get_now, get_today, to_db_date
from modules.dates import repository
from modules.dates.errors import EventAlreadyExistsError
from modules.dates.types import (
    DateAttribute,
    DateCouple,
    DateEvent,
    DateEventStatus,
    DateMemoryKind,
    DateOperationResult,
    DateOperationStatus,
)
from modules.reminders.service import (
    create_system_reminder,
    delete_system_reminders_by_entity,
)
from modules.users.repository import get_active_user_by_id

_DATE_REGEX = "%Y-%m-%d"
_DATETIME_REGEX = "%Y-%m-%dT%H:%M"
_REVEALABLE_ATTRIBUTE_KEYS = {"place", "dresscode", "vibes"}
_MILESTONE_TYPES = {"monthly", "anniversary", "wedding", "custom"}
_RELATIONSHIP_STATUSES = {"couple", "married"}
_COUPLE_STATUSES = {"active", "archived"}


def _is_valid_date(value: str) -> bool:
    try:
        datetime.strptime(value, _DATE_REGEX)
        return True
    except ValueError:
        return False


def _is_valid_datetime(value: str) -> bool:
    try:
        datetime.strptime(value, _DATETIME_REGEX)
        return True
    except ValueError:
        return False


def is_valid_reveal_on(value: str | None) -> bool:
    if value is None:
        return True
    return _is_valid_date(value) or _is_valid_datetime(value)


def _reveal_threshold(reveal_on: str | None):
    if reveal_on is None:
        return None
    if _is_valid_datetime(reveal_on):
        return datetime.strptime(reveal_on, _DATETIME_REGEX)
    return datetime.strptime(reveal_on, _DATE_REGEX)


def _attribute_visible_for(
    attribute: DateAttribute,
    viewer_user_id: int,
    event_planned_by: int,
    now,
    today,
) -> bool:
    if not attribute.is_secret:
        return True
    if viewer_user_id == event_planned_by:
        return True
    if attribute.reveal_on is None:
        return False
    if _is_valid_datetime(attribute.reveal_on):
        return now >= datetime.strptime(attribute.reveal_on, _DATETIME_REGEX)
    return today >= datetime.strptime(attribute.reveal_on, _DATE_REGEX).date()


def _is_member(couple: DateCouple, user_id: int) -> bool:
    return user_id in couple.member_ids


def _validator_members(member_ids) -> DateOperationStatus | None:
    if not isinstance(member_ids, list) or not member_ids:
        return DateOperationStatus.EMPTY_MEMBERS
    for member_id in member_ids:
        if not isinstance(member_id, int) or isinstance(member_id, bool):
            return DateOperationStatus.INVALID_MEMBERS
        user = get_active_user_by_id(member_id)
        if user is None:
            return DateOperationStatus.INVALID_MEMBERS
    if len(set(member_ids)) != len(member_ids):
        return DateOperationStatus.INVALID_MEMBERS
    return None


# Couples


def create_couple(
    member_ids: list[int],
    started_at: str | None = None,
    relationship_status: str = "couple",
) -> DateOperationResult:
    member_error = _validator_members(member_ids)
    if member_error is not None:
        return DateOperationResult(status=member_error)

    if started_at is not None and not _is_valid_date(started_at):
        return DateOperationResult(status=DateOperationStatus.INVALID_STARTED_AT)

    if relationship_status not in _RELATIONSHIP_STATUSES:
        return DateOperationResult(status=DateOperationStatus.INVALID_RELATIONSHIP_STATUS)

    now = to_db_date(get_today())
    couple = repository.create_couple(
        created_at=now,
        updated_at=now,
        started_at=started_at,
        relationship_status=relationship_status,
    )
    repository.replace_couple_members(couple.id, member_ids)
    return DateOperationResult(couple=repository.get_couple_by_id(couple.id))


def get_couples(include_archived: bool = False) -> DateOperationResult:
    status = None if include_archived else "active"
    return DateOperationResult(couples=repository.get_couples(status=status))


def update_couple(
    couple_id: int,
    viewer_user_id: int,
    member_ids: list[int] | None = None,
    started_at: str | None = None,
    relationship_status: str | None = None,
    status: str | None = None,
) -> DateOperationResult:
    couple = repository.get_couple_by_id(couple_id)
    if couple is None:
        return DateOperationResult(status=DateOperationStatus.NOT_FOUND)
    if not _is_member(couple, viewer_user_id):
        return DateOperationResult(status=DateOperationStatus.FORBIDDEN)

    if member_ids is not None:
        member_error = _validator_members(member_ids)
        if member_error is not None:
            return DateOperationResult(status=member_error)

    if started_at is not None and not _is_valid_date(started_at):
        return DateOperationResult(status=DateOperationStatus.INVALID_STARTED_AT)

    if relationship_status is not None and relationship_status not in _RELATIONSHIP_STATUSES:
        return DateOperationResult(status=DateOperationStatus.INVALID_RELATIONSHIP_STATUS)

    if status is not None and status not in _COUPLE_STATUSES:
        return DateOperationResult(status=DateOperationStatus.INVALID_STATUS)

    now = to_db_date(get_today())
    repository.update_couple(
        couple_id,
        updated_at=now,
        started_at=started_at,
        relationship_status=relationship_status,
        status=status,
    )

    if member_ids is not None:
        repository.replace_couple_members(couple_id, member_ids)

    return DateOperationResult(couple=repository.get_couple_by_id(couple_id))


def delete_couple(couple_id: int) -> DateOperationResult:
    couple = repository.get_couple_by_id(couple_id)
    if couple is None:
        return DateOperationResult(status=DateOperationStatus.NOT_FOUND)
    repository.delete_couple(couple_id)
    return DateOperationResult()


# Milestones


def create_milestone(
    couple_id: int,
    viewer_user_id: int,
    milestone_type: str,
    date: str,
    label: str,
    notes: str | None = None,
) -> DateOperationResult:
    couple = repository.get_couple_by_id(couple_id)
    if couple is None:
        return DateOperationResult(status=DateOperationStatus.NOT_FOUND)
    if not _is_member(couple, viewer_user_id):
        return DateOperationResult(status=DateOperationStatus.FORBIDDEN)

    if milestone_type not in _MILESTONE_TYPES:
        return DateOperationResult(status=DateOperationStatus.INVALID_MILESTONE_TYPE)
    if not _is_valid_date(date):
        return DateOperationResult(status=DateOperationStatus.INVALID_MILESTONE_DATE)
    if not isinstance(label, str) or not label.strip():
        return DateOperationResult(status=DateOperationStatus.INVALID_MILESTONE_LABEL)

    milestone = repository.create_milestone(
        couple_id=couple_id,
        milestone_type=milestone_type,
        date=date,
        label=label.strip(),
        created_at=to_db_date(get_today()),
        notes=notes,
    )
    return DateOperationResult(milestone=milestone)


def list_milestones(couple_id: int, viewer_user_id: int) -> DateOperationResult:
    couple = repository.get_couple_by_id(couple_id)
    if couple is None:
        return DateOperationResult(status=DateOperationStatus.NOT_FOUND)
    if not _is_member(couple, viewer_user_id):
        return DateOperationResult(status=DateOperationStatus.FORBIDDEN)
    return DateOperationResult(milestones=repository.list_milestones(couple_id))


def delete_milestone(milestone_id: int, viewer_user_id: int) -> DateOperationResult:
    milestone = repository.get_milestone_by_id(milestone_id)
    if milestone is None:
        return DateOperationResult(status=DateOperationStatus.NOT_FOUND)
    couple = repository.get_couple_by_id(milestone.couple_id)
    if not _is_member(couple, viewer_user_id):
        return DateOperationResult(status=DateOperationStatus.FORBIDDEN)
    repository.delete_milestone(milestone_id)
    return DateOperationResult()


def _cleanup_event_reminders(event: DateEvent) -> None:
    try:
        couple = repository.get_couple_by_id(event.couple_id)
    except Exception:
        couple = None
    targets = couple.member_ids if couple else [event.planned_by]
    for target in targets:
        delete_system_reminders_by_entity(
            target, "dates:plan", str(event.id)
        )
        delete_system_reminders_by_entity(
            target, "dates:event", str(event.id)
        )


def _create_plan_reminder(event: DateEvent) -> None:
    if event.week_start <= to_db_date(get_today()):
        return
    create_system_reminder(
        system_ref_entity="dates:plan",
        system_ref_entity_id=str(event.id),
        user_id=event.planned_by,
        message="🌹 Esta semana te toca planear la cita de pareja 💕",
        trigger_at=event.week_start,
    )


def _event_message(event: DateEvent, target_user_id: int) -> str:
    now = get_now()
    today = now.date()
    visible = [
        a
        for a in event.attributes
        if a.key in _REVEALABLE_ATTRIBUTE_KEYS
        and _attribute_visible_for(a, target_user_id, event.planned_by, now, today)
    ]
    lines = ["💕 Hoy es la cita de pareja!"]
    if event.title:
        lines.append(f"📌 {event.title}")
    time_part = f" a las {event.scheduled_time}" if event.scheduled_time else ""
    if event.scheduled_date:
        lines.append(f"📅 {event.scheduled_date}{time_part}")
    for attr in visible:
        emoji = _attribute_emoji(attr.key)
        lines.append(f"{emoji} {attr.key.title()}: {attr.value}")
    return "\n".join(lines)


def _attribute_emoji(key: str) -> str:
    return {
        "place": "📍",
        "dresscode": "👗",
        "vibes": "✨",
    }.get(key, "•")


def _create_event_reminder(event: DateEvent) -> None:
    if not event.scheduled_date or event.scheduled_date < to_db_date(get_today()):
        return
    couple = repository.get_couple_by_id(event.couple_id)
    targets = couple.member_ids if couple else [event.planned_by]
    for target in targets:
        delete_system_reminders_by_entity(target, "dates:event", str(event.id))
        create_system_reminder(
            system_ref_entity="dates:event",
            system_ref_entity_id=str(event.id),
            user_id=target,
            message=_event_message(event, target),
            trigger_at=event.scheduled_date,
            trigger_time=event.scheduled_time,
        )


def _validate_attributes(attributes) -> DateOperationStatus | None:
    if not isinstance(attributes, list):
        return DateOperationStatus.INVALID_ATTRIBUTES
    for attr in attributes:
        if not isinstance(attr, dict):
            return DateOperationStatus.INVALID_ATTRIBUTES
        key = attr.get("key")
        value = attr.get("value")
        if not isinstance(key, str) or not key.strip():
            return DateOperationStatus.INVALID_ATTRIBUTES
        if not isinstance(value, str):
            return DateOperationStatus.INVALID_ATTRIBUTES
        if "reveal_on" in attr and not is_valid_reveal_on(attr.get("reveal_on")):
            return DateOperationStatus.INVALID_REVEAL_ON
    return None


def who_plans_next(couple_id: int) -> int | None:
    couple = repository.get_couple_by_id(couple_id)
    if couple is None or not couple.member_ids:
        return None
    if len(couple.member_ids) == 1:
        return couple.member_ids[0]
    last_event = repository.get_last_event(couple_id)
    if last_event is None:
        return couple.member_ids[0]
    ordered = list(couple.member_ids)
    try:
        last_index = ordered.index(last_event.planned_by)
    except ValueError:
        return ordered[0]
    return ordered[(last_index + 1) % len(ordered)]


# Events


def create_event(
    couple_id: int,
    week_start: str,
    viewer_user_id: int,
    planned_by: int | None = None,
    title: str | None = None,
    scheduled_date: str | None = None,
    scheduled_time: str | None = None,
    attributes: list[dict] | None = None,
) -> DateOperationResult:
    couple = repository.get_couple_by_id(couple_id)
    if couple is None:
        return DateOperationResult(status=DateOperationStatus.NOT_FOUND)
    if not _is_member(couple, viewer_user_id):
        return DateOperationResult(status=DateOperationStatus.FORBIDDEN)

    if not _is_valid_date(week_start):
        return DateOperationResult(status=DateOperationStatus.INVALID_WEEK_START)

    if planned_by is not None:
        if not _is_member(couple, planned_by):
            return DateOperationResult(status=DateOperationStatus.INVALID_PLANNED_BY)
    else:
        planned_by = who_plans_next(couple_id)
        if planned_by is None:
            return DateOperationResult(status=DateOperationStatus.EMPTY_MEMBERS)

    if scheduled_date is not None and not _is_valid_date(scheduled_date):
        return DateOperationResult(status=DateOperationStatus.INVALID_SCHEDULED_DATE)
    if scheduled_time is not None:
        try:
            datetime.strptime(scheduled_time, "%H:%M")
        except ValueError:
            return DateOperationResult(status=DateOperationStatus.INVALID_SCHEDULED_TIME)

    if attributes is not None:
        attr_error = _validate_attributes(attributes)
        if attr_error is not None:
            return DateOperationResult(status=attr_error)

    now = to_db_date(get_today())
    try:
        event = repository.create_event(
            couple_id=couple_id,
            week_start=week_start,
            planned_by=planned_by,
            created_at=now,
            updated_at=now,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            title=title.strip() if title else None,
        )
    except EventAlreadyExistsError:
        return DateOperationResult(status=DateOperationStatus.DUPLICATE_WEEK)

    if attributes is not None:
        repository.replace_event_attributes(
            event.id,
            [
                (
                    attr["key"].strip(),
                    attr["value"],
                    bool(attr.get("is_secret", False)),
                    attr.get("reveal_on") if attr.get("is_secret", False) else None,
                )
                for attr in attributes
            ],
        )

    event = repository.get_event_by_id(event.id)
    status = (
        DateEventStatus.SCHEDULED
        if event.scheduled_date is not None
        else DateEventStatus.PLANNED
    )
    repository.update_event(event.id, now, status=status.value)
    event = repository.get_event_by_id(event.id)

    _create_plan_reminder(event)
    _create_event_reminder(event)
    return DateOperationResult(event=event)


def list_events(
    viewer_user_id: int,
    couple_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> DateOperationResult:
    if couple_id is not None:
        couple = repository.get_couple_by_id(couple_id)
        if couple is not None and not _is_member(couple, viewer_user_id):
            return DateOperationResult(status=DateOperationStatus.FORBIDDEN)
    else:
        couples = repository.get_couples()
        visible_couple_ids = [
            c.id for c in couples if _is_member(c, viewer_user_id)
        ]
        if not visible_couple_ids:
            return DateOperationResult(events=[])
        events = []
        for cid in visible_couple_ids:
            events.extend(
                repository.list_events(
                    couple_id=cid, from_date=from_date, to_date=to_date
                )
            )
        events.sort(key=lambda e: e.week_start)
        return DateOperationResult(events=events)

    events = repository.list_events(
        couple_id=couple_id, from_date=from_date, to_date=to_date
    )
    return DateOperationResult(events=events)


def _apply_visibility(event: DateEvent, viewer_user_id: int) -> DateEvent:
    now = get_now()
    today = now.date()
    event.attributes = [
        a
        for a in event.attributes
        if _attribute_visible_for(a, viewer_user_id, event.planned_by, now, today)
    ]
    return event


def get_event_detail(event_id: int, viewer_user_id: int) -> DateOperationResult:
    event = repository.get_event_by_id(event_id)
    if event is None:
        return DateOperationResult(status=DateOperationStatus.NOT_FOUND)
    couple = repository.get_couple_by_id(event.couple_id)
    if not _is_member(couple, viewer_user_id):
        return DateOperationResult(status=DateOperationStatus.FORBIDDEN)
    return DateOperationResult(event=_apply_visibility(event, viewer_user_id))


def update_event(
    event_id: int,
    viewer_user_id: int,
    planned_by: int | None = None,
    scheduled_date: str | None = None,
    scheduled_time: str | None = None,
    title: str | None = None,
    attributes: list[dict] | None = None,
) -> DateOperationResult:
    event = repository.get_event_by_id(event_id)
    if event is None:
        return DateOperationResult(status=DateOperationStatus.NOT_FOUND)
    couple = repository.get_couple_by_id(event.couple_id)
    if not _is_member(couple, viewer_user_id):
        return DateOperationResult(status=DateOperationStatus.FORBIDDEN)

    now = to_db_date(get_today())
    fields: dict = {}

    if planned_by is not None:
        if not _is_member(couple, planned_by):
            return DateOperationResult(status=DateOperationStatus.INVALID_PLANNED_BY)
        fields["planned_by"] = planned_by

    if scheduled_date is not None and not _is_valid_date(scheduled_date):
        return DateOperationResult(status=DateOperationStatus.INVALID_SCHEDULED_DATE)
    if scheduled_time is not None:
        try:
            datetime.strptime(scheduled_time, "%H:%M")
        except ValueError:
            return DateOperationResult(status=DateOperationStatus.INVALID_SCHEDULED_TIME)

    if scheduled_date is not None:
        fields["scheduled_date"] = scheduled_date
    if scheduled_time is not None:
        fields["scheduled_time"] = scheduled_time

    if title is not None:
        title = title.strip()
        fields["title"] = title if title else None

    if attributes is not None:
        attr_error = _validate_attributes(attributes)
        if attr_error is not None:
            return DateOperationResult(status=attr_error)

    if fields:
        repository.update_event(event_id, now, **fields)

    if attributes is not None:
        repository.replace_event_attributes(
            event_id,
            [
                (
                    attr["key"].strip(),
                    attr["value"],
                    bool(attr.get("is_secret", False)),
                    attr.get("reveal_on") if attr.get("is_secret", False) else None,
                )
                for attr in attributes
            ],
        )

    event = repository.get_event_by_id(event_id)
    effective_scheduled_date = (
        scheduled_date if scheduled_date is not None else event.scheduled_date
    )
    effective_time = scheduled_time if scheduled_time is not None else event.scheduled_time
    if effective_scheduled_date is not None:
        repository.update_event(
            event_id,
            now,
            status=DateEventStatus.SCHEDULED.value,
            scheduled_date=effective_scheduled_date,
            scheduled_time=effective_time,
        )
    else:
        repository.update_event(event_id, now, status=DateEventStatus.PLANNED.value)

    event = repository.get_event_by_id(event_id)
    _create_plan_reminder(event)
    _create_event_reminder(event)
    return DateOperationResult(event=_apply_visibility(event, viewer_user_id))


def complete_event(event_id: int, viewer_user_id: int) -> DateOperationResult:
    event = repository.get_event_by_id(event_id)
    if event is None:
        return DateOperationResult(status=DateOperationStatus.NOT_FOUND)
    couple = repository.get_couple_by_id(event.couple_id)
    if not _is_member(couple, viewer_user_id):
        return DateOperationResult(status=DateOperationStatus.FORBIDDEN)

    now = to_db_date(get_today())
    repository.update_event(event_id, now, status=DateEventStatus.DONE.value)
    _cleanup_event_reminders(event)
    return DateOperationResult(event=repository.get_event_by_id(event_id))


def delete_event(event_id: int, viewer_user_id: int) -> DateOperationResult:
    event = repository.get_event_by_id(event_id)
    if event is None:
        return DateOperationResult(status=DateOperationStatus.NOT_FOUND)
    couple = repository.get_couple_by_id(event.couple_id)
    if not _is_member(couple, viewer_user_id):
        return DateOperationResult(status=DateOperationStatus.FORBIDDEN)
    _cleanup_event_reminders(event)
    repository.delete_event(event_id)
    return DateOperationResult()


# Memories


def add_memory(
    event_id: int,
    viewer_user_id: int,
    kind: str,
    media_url: str | None = None,
    caption: str | None = None,
    taken_by: int | None = None,
) -> DateOperationResult:
    event = repository.get_event_by_id(event_id)
    if event is None:
        return DateOperationResult(status=DateOperationStatus.NOT_FOUND)
    couple = repository.get_couple_by_id(event.couple_id)
    if not _is_member(couple, viewer_user_id):
        return DateOperationResult(status=DateOperationStatus.FORBIDDEN)

    try:
        DateMemoryKind(kind)
    except ValueError:
        return DateOperationResult(status=DateOperationStatus.INVALID_KIND)

    if kind == DateMemoryKind.PHOTO.value and not media_url:
        return DateOperationResult(status=DateOperationStatus.INVALID_MEDIA_URL)

    if taken_by is not None and not _is_member(couple, taken_by):
        return DateOperationResult(status=DateOperationStatus.INVALID_MEMBERS)

    memory = repository.create_memory(
        event_id=event_id,
        kind=kind,
        created_at=to_db_date(get_today()),
        media_url=media_url,
        caption=caption,
        taken_by=taken_by,
    )
    return DateOperationResult(memory=memory)


def list_memories(event_id: int, viewer_user_id: int) -> DateOperationResult:
    event = repository.get_event_by_id(event_id)
    if event is None:
        return DateOperationResult(status=DateOperationStatus.NOT_FOUND)
    couple = repository.get_couple_by_id(event.couple_id)
    if not _is_member(couple, viewer_user_id):
        return DateOperationResult(status=DateOperationStatus.FORBIDDEN)
    return DateOperationResult(memories=repository.list_memories(event_id))


def delete_memory(memory_id: int, viewer_user_id: int) -> DateOperationResult:
    memory = repository.get_memory_by_id(memory_id)
    if memory is None:
        return DateOperationResult(status=DateOperationStatus.NOT_FOUND)
    event = repository.get_event_by_id(memory.event_id)
    couple = repository.get_couple_by_id(event.couple_id)
    if not _is_member(couple, viewer_user_id):
        return DateOperationResult(status=DateOperationStatus.FORBIDDEN)
    repository.delete_memory(memory_id)
    return DateOperationResult()
