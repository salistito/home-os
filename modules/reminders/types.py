from dataclasses import dataclass
from enum import StrEnum


class ReminderRecurrence(StrEnum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class ReminderOperationStatus(StrEnum):
    OK = "ok"
    INVALID = "invalid"
    PAST_TIME = "past_time"
    DUPLICATE_MESSAGE = "duplicate_message"
    NOT_FOUND = "not_found"


@dataclass
class Reminder:
    id: int
    user_id: str
    message: str
    trigger_at: str
    trigger_time: str | None
    recurrence: ReminderRecurrence
    cron_job_id: str | None
    created_at: str


@dataclass
class ReminderOperationResult:
    reminder: Reminder | None
    status: ReminderOperationStatus
