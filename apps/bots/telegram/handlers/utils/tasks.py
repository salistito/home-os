from core.utils.string import html_escape
from modules.tasks.types import TaskOperationStatus

from apps.bots.telegram.messages_es import (
    add_task_usage,
    delete_task_usage,
    edit_task_usage,
    task_created,
    task_deleted,
    task_duplicate_name,
    task_has_assignments_error,
    task_invalid_frequency,
    task_invalid_name,
    task_invalid_points,
    task_not_found_by_name,
    task_updated,
)

EDITABLE_TASK_PROPS = {"name": "name", "points": "points", "freq": "frequency_days"}


def parse_add_task_args(text: str) -> tuple[str, int, int | None] | None:
    args = text.split()  # /add_task <name> <points> [freq]
    if len(args) < 3:
        return None

    if len(args) == 3:
        try:
            points = int(args[-1])
        except ValueError:
            return None
        freq = None

    elif len(args) >= 4:
        try:
            freq = int(args[-1])
            points = int(args[-2])
        except ValueError:
            try:
                points = int(args[-1])
            except ValueError:
                return None
            freq = None

    task_name_end = -2 if freq is not None else -1
    task_name = " ".join(args[1:task_name_end])
    return html_escape(task_name), points, freq


def parse_edit_task_args(text: str) -> tuple[str, str, str] | None:
    args = text.split()  # /edit_task <name> <field> <value>
    if len(args) < 4:
        return None

    for i in range(1, len(args) - 1):
        if args[i] in EDITABLE_TASK_PROPS:
            task_name = " ".join(args[1:i])
            field = args[i]
            value = " ".join(args[i + 1 :])
            if not task_name or not value:
                return None
            return html_escape(task_name), field, html_escape(value)

    return None


def parse_delete_task_args(text: str) -> str | None:
    args = text.split()  # /delete_task <name>
    if len(args) < 2:
        return None
    task_name = " ".join(args[1:])
    return html_escape(task_name)


def coerce_edit_value(db_field: str, value: str) -> object:
    if db_field == "points":
        return int(value)
    if db_field == "frequency_days":
        return None if value in ("0", "-") else int(value)
    return value


def _common_task_errors(result) -> str | None:
    match result.status:
        case TaskOperationStatus.INVALID_NAME:
            return task_invalid_name()
        case TaskOperationStatus.INVALID_POINTS:
            return task_invalid_points()
        case TaskOperationStatus.INVALID_FREQUENCY:
            return task_invalid_frequency()
        case TaskOperationStatus.DUPLICATE_NAME:
            return task_duplicate_name(result.task.name)
    return None


def add_task_reply(result) -> str:
    if msg := _common_task_errors(result):
        return msg
    if result.status is TaskOperationStatus.OK:
        return task_created(result.task)
    return add_task_usage()


def update_task_reply(result, task_name: str, field: str, old_value: str, new_value: str) -> str:
    if msg := _common_task_errors(result):
        return msg
    match result.status:
        case TaskOperationStatus.OK:
            return task_updated(result.task.name, field, old_value, new_value)
        case TaskOperationStatus.NOT_FOUND:
            return task_not_found_by_name(task_name)
    return edit_task_usage()


def delete_task_reply(result, task_name: str) -> str:
    match result.status:
        case TaskOperationStatus.OK:
            return task_deleted(result.task.name)
        case TaskOperationStatus.NOT_FOUND:
            return task_not_found_by_name(task_name)
        case TaskOperationStatus.HAS_ASSIGNMENTS:
            return task_has_assignments_error(result.task.name)
    return delete_task_usage()
