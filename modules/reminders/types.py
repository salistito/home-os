from dataclasses import dataclass
from enum import StrEnum

from modules.reminders.system import SystemRef


class ReminderOwner(StrEnum):
    USER = "user"
    SYSTEM = "system"


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
    user_id: int
    message: str
    trigger_at: str
    trigger_time: str | None
    recurrence: ReminderRecurrence
    cron_job_id: str | None
    created_at: str
    owner: ReminderOwner = ReminderOwner.USER
    system_ref_entity: str | None = None
    system_ref_entity_id: str | None = None

    @property
    def system_ref(self) -> SystemRef | None:
        if self.system_ref_entity is None or self.system_ref_entity_id is None:
            return None
        return SystemRef.parse(self.system_ref_entity)


@dataclass
class ReminderOperationResult:
    reminder: Reminder | None = None
    status: ReminderOperationStatus
