from dataclasses import dataclass
from enum import StrEnum


class BreakModule(StrEnum):
    TASKS = "tasks"
    FINANCES = "finances"
    FOOD = "food"
    FITNESS = "fitness"
    REMINDERS = "reminders"

    @classmethod
    def values(cls) -> list[str]:
        return [module.value for module in cls]


class BreakPeriodOperationStatus(StrEnum):
    OK = "ok"
    INVALID_START_DATE = "invalid_start_date"
    INVALID_END_DATE = "invalid_end_date"
    INVALID_DATE_RANGE = "invalid_date_range"
    INVALID_USER_IDS = "invalid_user_ids"
    INVALID_MODULES = "invalid_modules"
    NOT_FOUND = "not_found"


@dataclass
class BreakPeriod:
    id: int
    label: str | None
    start_date: str
    end_date: str | None
    created_at: str
    user_ids: list[int] | None = None
    modules: list[str] | None = None


@dataclass
class BreakPeriodOperationResult:
    status: BreakPeriodOperationStatus
    break_period: BreakPeriod | None = None
