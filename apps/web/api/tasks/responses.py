from http import HTTPStatus

from starlette.responses import JSONResponse

from modules.tasks.types import Task, TaskOperationStatus

_STATUS_HTTP = {
    TaskOperationStatus.INVALID_NAME: HTTPStatus.BAD_REQUEST,
    TaskOperationStatus.INVALID_POINTS: HTTPStatus.BAD_REQUEST,
    TaskOperationStatus.INVALID_FREQUENCY: HTTPStatus.BAD_REQUEST,
    TaskOperationStatus.DUPLICATE_NAME: HTTPStatus.BAD_REQUEST,
    TaskOperationStatus.HAS_ASSIGNMENTS: HTTPStatus.CONFLICT,
    TaskOperationStatus.NOT_FOUND: HTTPStatus.NOT_FOUND,
}

_STATUS_MESSAGE = {
    TaskOperationStatus.INVALID_NAME: "Task name cannot be empty.",
    TaskOperationStatus.INVALID_POINTS: "Points must be greater than 0.",
    TaskOperationStatus.INVALID_FREQUENCY: (
        "Frequency must be greater than 0 and recurring tasks require a start date."
    ),
    TaskOperationStatus.DUPLICATE_NAME: "A task with that name already exists.",
    TaskOperationStatus.HAS_ASSIGNMENTS: ("Cannot delete a task with pending assignments."),
    TaskOperationStatus.NOT_FOUND: "Task not found.",
}


def serialize_task(task: Task) -> dict:
    return {
        "id": task.id,
        "name": task.name,
        "points": task.points,
        "frequency_days": task.frequency_days,
        "next_due_date": task.next_due_date,
    }


def error_response(status: TaskOperationStatus) -> JSONResponse:
    return JSONResponse(
        {"error": status.value, "message": _STATUS_MESSAGE[status]},
        status_code=_STATUS_HTTP[status],
    )
