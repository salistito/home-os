from dataclasses import dataclass
from enum import StrEnum


class AssignmentCompletionStatus(StrEnum):
    OK = "ok"
    ALREADY_DONE = "already_done"
    NOT_FOUND = "not_found"


@dataclass
class Task:
    id: int
    name: str
    points: int
    frequency_days: int | None
    next_due_date: str | None


@dataclass
class Assignment:
    task_id: int
    task_name: str
    user_id: str
    points: int


@dataclass
class AssignmentCompletionResult:
    task_name: str | None
    status: AssignmentCompletionStatus
    points_awarded: int
