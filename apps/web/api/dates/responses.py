from http import HTTPStatus

from starlette.responses import JSONResponse

from modules.dates.types import (
    DateAttribute,
    DateCouple,
    DateEvent,
    DateMemory,
    DateMilestone,
    DateOperationStatus,
)

_STATUS_HTTP = {
    DateOperationStatus.INVALID_MEMBERS: HTTPStatus.BAD_REQUEST,
    DateOperationStatus.EMPTY_MEMBERS: HTTPStatus.BAD_REQUEST,
    DateOperationStatus.INVALID_STARTED_AT: HTTPStatus.BAD_REQUEST,
    DateOperationStatus.INVALID_RELATIONSHIP_STATUS: HTTPStatus.BAD_REQUEST,
    DateOperationStatus.INVALID_STATUS: HTTPStatus.BAD_REQUEST,
    DateOperationStatus.INVALID_MILESTONE_TYPE: HTTPStatus.BAD_REQUEST,
    DateOperationStatus.INVALID_MILESTONE_DATE: HTTPStatus.BAD_REQUEST,
    DateOperationStatus.INVALID_MILESTONE_LABEL: HTTPStatus.BAD_REQUEST,
    DateOperationStatus.INVALID_TITLE: HTTPStatus.BAD_REQUEST,
    DateOperationStatus.INVALID_WEEK_START: HTTPStatus.BAD_REQUEST,
    DateOperationStatus.INVALID_PLANNED_BY: HTTPStatus.BAD_REQUEST,
    DateOperationStatus.INVALID_SCHEDULED_DATE: HTTPStatus.BAD_REQUEST,
    DateOperationStatus.INVALID_SCHEDULED_TIME: HTTPStatus.BAD_REQUEST,
    DateOperationStatus.INVALID_ATTRIBUTES: HTTPStatus.BAD_REQUEST,
    DateOperationStatus.INVALID_REVEAL_ON: HTTPStatus.BAD_REQUEST,
    DateOperationStatus.INVALID_KIND: HTTPStatus.BAD_REQUEST,
    DateOperationStatus.INVALID_MEDIA_URL: HTTPStatus.BAD_REQUEST,
    DateOperationStatus.DUPLICATE_WEEK: HTTPStatus.CONFLICT,
    DateOperationStatus.FORBIDDEN: HTTPStatus.FORBIDDEN,
    DateOperationStatus.NOT_FOUND: HTTPStatus.NOT_FOUND,
}

_STATUS_MESSAGE = {
    DateOperationStatus.INVALID_MEMBERS: "Uno o más miembros no son usuarios activos válidos.",
    DateOperationStatus.EMPTY_MEMBERS: "Una pareja necesita al menos un miembro.",
    DateOperationStatus.INVALID_STARTED_AT: (
        "started_at debe ser una fecha ISO (YYYY-MM-DD) o null."
    ),
    DateOperationStatus.INVALID_RELATIONSHIP_STATUS: (
        "relationship_status debe ser 'couple' o 'married'."
    ),
    DateOperationStatus.INVALID_STATUS: "status debe ser 'active' o 'archived'.",
    DateOperationStatus.INVALID_MILESTONE_TYPE: (
        "El tipo del hito debe ser 'monthly', 'anniversary', 'wedding' o 'custom'."
    ),
    DateOperationStatus.INVALID_MILESTONE_DATE: (
        "La fecha del hito debe ser ISO (YYYY-MM-DD)."
    ),
    DateOperationStatus.INVALID_MILESTONE_LABEL: (
        "El hito necesita una etiqueta (label)."
    ),
    DateOperationStatus.INVALID_TITLE: "El título no es válido.",
    DateOperationStatus.INVALID_WEEK_START: "week_start debe ser una fecha ISO (YYYY-MM-DD).",
    DateOperationStatus.INVALID_PLANNED_BY: "planned_by debe ser un miembro de la pareja.",
    DateOperationStatus.INVALID_SCHEDULED_DATE: (
        "scheduled_date debe ser una fecha ISO (YYYY-MM-DD)."
    ),
    DateOperationStatus.INVALID_SCHEDULED_TIME: "scheduled_time debe ser HH:MM.",
    DateOperationStatus.INVALID_ATTRIBUTES: (
        "attributes debe ser una lista de {key, value, is_secret?, reveal_on?}."
    ),
    DateOperationStatus.INVALID_REVEAL_ON: (
        "reveal_on debe ser YYYY-MM-DD, YYYY-MM-DDTHH:MM o null."
    ),
    DateOperationStatus.INVALID_KIND: "kind debe ser 'photo' o 'note'.",
    DateOperationStatus.INVALID_MEDIA_URL: "Un recuerdo de tipo photo requiere media_url.",
    DateOperationStatus.DUPLICATE_WEEK: "Ya existe una cita para esa semana de esa pareja.",
    DateOperationStatus.FORBIDDEN: "No tienes acceso a esta pareja.",
    DateOperationStatus.NOT_FOUND: "No encontrado.",
}


def _serialize_attribute(attr: DateAttribute) -> dict:
    return {
        "id": attr.id,
        "key": attr.key,
        "value": attr.value,
        "is_secret": attr.is_secret,
        "reveal_on": attr.reveal_on,
    }


def serialize_couple(couple: DateCouple) -> dict:
    return {
        "id": couple.id,
        "member_ids": couple.member_ids,
        "started_at": couple.started_at,
        "relationship_status": couple.relationship_status,
        "status": couple.status,
        "created_at": couple.created_at,
        "updated_at": couple.updated_at,
    }


def serialize_milestone(milestone: DateMilestone) -> dict:
    return {
        "id": milestone.id,
        "couple_id": milestone.couple_id,
        "type": milestone.type,
        "date": milestone.date,
        "label": milestone.label,
        "notes": milestone.notes,
        "created_at": milestone.created_at,
    }


def serialize_event(event: DateEvent) -> dict:
    return {
        "id": event.id,
        "couple_id": event.couple_id,
        "week_start": event.week_start,
        "planned_by": event.planned_by,
        "scheduled_date": event.scheduled_date,
        "scheduled_time": event.scheduled_time,
        "title": event.title,
        "status": event.status,
        "created_at": event.created_at,
        "updated_at": event.updated_at,
        "attributes": [_serialize_attribute(a) for a in event.attributes],
    }


def serialize_memory(memory: DateMemory) -> dict:
    return {
        "id": memory.id,
        "event_id": memory.event_id,
        "kind": memory.kind,
        "media_url": memory.media_url,
        "caption": memory.caption,
        "taken_by": memory.taken_by,
        "created_at": memory.created_at,
    }


def error_response(status: DateOperationStatus) -> JSONResponse:
    return JSONResponse(
        {"error": status.value, "message": _STATUS_MESSAGE.get(status, "Error inesperado.")},
        status_code=_STATUS_HTTP.get(status, HTTPStatus.BAD_REQUEST),
    )
