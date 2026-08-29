from dataclasses import dataclass, field
from enum import StrEnum


class DateEventStatus(StrEnum):
    PLANNED = "planned"
    SCHEDULED = "scheduled"
    DONE = "done"


class DateMemoryKind(StrEnum):
    PHOTO = "photo"
    NOTE = "note"


class DateOperationStatus(StrEnum):
    OK = "ok"
    NOT_FOUND = "not_found"
    FORBIDDEN = "forbidden"
    INVALID_MEMBERS = "invalid_members"
    EMPTY_MEMBERS = "empty_members"
    INVALID_STARTED_AT = "invalid_started_at"
    INVALID_RELATIONSHIP_STATUS = "invalid_relationship_status"
    INVALID_STATUS = "invalid_status"
    INVALID_MILESTONE_TYPE = "invalid_milestone_type"
    INVALID_MILESTONE_DATE = "invalid_milestone_date"
    INVALID_MILESTONE_LABEL = "invalid_milestone_label"
    INVALID_TITLE = "invalid_title"
    INVALID_WEEK_START = "invalid_week_start"
    INVALID_PLANNED_BY = "invalid_planned_by"
    INVALID_SCHEDULED_DATE = "invalid_scheduled_date"
    INVALID_SCHEDULED_TIME = "invalid_scheduled_time"
    INVALID_ATTRIBUTES = "invalid_attributes"
    INVALID_REVEAL_ON = "invalid_reveal_on"
    INVALID_KIND = "invalid_kind"
    INVALID_MEDIA_URL = "invalid_media_url"
    DUPLICATE_WEEK = "duplicate_week"


@dataclass
class DateCouple:
    id: int
    member_ids: list[int] = field(default_factory=list)
    started_at: str | None = None
    relationship_status: str = "couple"
    status: str = "active"
    created_at: str = ""
    updated_at: str = ""


@dataclass
class DateMilestone:
    id: int
    couple_id: int
    type: str
    date: str
    label: str
    notes: str | None = None
    created_at: str = ""


@dataclass
class DateAttribute:
    id: int
    event_id: int
    key: str
    value: str
    is_secret: bool = False
    reveal_on: str | None = None


@dataclass
class DateEvent:
    id: int
    couple_id: int
    week_start: str
    planned_by: int
    scheduled_date: str | None = None
    scheduled_time: str | None = None
    title: str | None = None
    status: str = DateEventStatus.PLANNED
    created_at: str = ""
    updated_at: str = ""
    attributes: list[DateAttribute] = field(default_factory=list)


@dataclass
class DateMemory:
    id: int
    event_id: int
    kind: str
    media_url: str | None = None
    caption: str | None = None
    taken_by: int | None = None
    created_at: str = ""


@dataclass
class DateOperationResult:
    status: DateOperationStatus = DateOperationStatus.OK
    couple: DateCouple | None = None
    couples: list[DateCouple] = field(default_factory=list)
    event: DateEvent | None = None
    events: list[DateEvent] = field(default_factory=list)
    memory: DateMemory | None = None
    memories: list[DateMemory] = field(default_factory=list)
    milestone: DateMilestone | None = None
    milestones: list[DateMilestone] = field(default_factory=list)
    planned_by: int | None = None
