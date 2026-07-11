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
    TaskOperationStatus.INVALID_NAME: "El nombre de la tarea no puede estar vacío.",
    TaskOperationStatus.INVALID_POINTS: "Los puntos deben ser mayores a 0.",
    TaskOperationStatus.INVALID_FREQUENCY: (
        "La frecuencia debe ser mayor a 0 y las tareas recurrentes necesitan "
        "una fecha de inicio."
    ),
    TaskOperationStatus.DUPLICATE_NAME: "Ya existe una tarea con ese nombre.",
    TaskOperationStatus.HAS_ASSIGNMENTS: (
        "No se puede borrar una tarea con asignaciones pendientes."
    ),
    TaskOperationStatus.NOT_FOUND: "No se encontró la tarea.",
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


def bad_request(message: str) -> JSONResponse:
    return JSONResponse(
        {"error": "invalid_request", "message": message},
        status_code=HTTPStatus.BAD_REQUEST,
    )
