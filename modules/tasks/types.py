from dataclasses import dataclass
from enum import StrEnum


class MarkTaskStatus(StrEnum):
    OK = "ok"
    NOT_FOUND = "not_found"


@dataclass
class Task:
    id: int
    name: str
    frequency_days: int | None
    points: int
    next_due_date: str | None


@dataclass
class Assignment:
    task_id: int
    task_name: str
    assignee_user_id: str
    points: int


@dataclass
class MarkTaskResult:
    status: MarkTaskStatus
    task_name: str | None
    points_awarded: int
