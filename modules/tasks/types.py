from dataclasses import dataclass
from enum import StrEnum


class TaskOperationStatus(StrEnum):
    OK = "ok"
    INVALID_NAME = "invalid_name"
    INVALID_POINTS = "invalid_points"
    INVALID_FREQUENCY = "invalid_frequency"
    DUPLICATE_NAME = "duplicate_name"
    HAS_ASSIGNMENTS = "has_assignments"
    NOT_FOUND = "not_found"


class AssignmentCompletionStatus(StrEnum):
    OK = "ok"
    ALREADY_DONE = "already_done"
    NOT_ASSIGNED = "not_assigned"
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
    user_id: int
    points: int


@dataclass
class TaskOperationResult:
    status: TaskOperationStatus
    task: Task | None = None


@dataclass
class AssignmentCompletionResult:
    status: AssignmentCompletionStatus
    task_name: str | None = None
    points_awarded: int = 0
