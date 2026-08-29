import json
from http import HTTPStatus

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.web.api.dates.responses import (
    error_response,
    serialize_couple,
    serialize_event,
    serialize_memory,
    serialize_milestone,
)
from apps.web.api.parsing import parse_int_param, parse_request_body
from apps.web.api.responses import bad_request
from modules.dates.service import (
    add_memory,
    complete_event,
    create_couple,
    create_event,
    create_milestone,
    delete_couple,
    delete_event,
    delete_memory,
    delete_milestone,
    get_couples,
    get_event_detail,
    list_events,
    list_memories,
    list_milestones,
    update_couple,
    update_event,
)
from modules.dates.types import DateOperationStatus


# Couples
async def create_couple_handler(request: Request) -> Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    member_ids = body.get("member_ids")
    if not isinstance(member_ids, list):
        return bad_request("member_ids is required.")

    result = create_couple(
        member_ids,
        started_at=body.get("started_at"),
        relationship_status=body.get("relationship_status"),
    )
    if result.status is not DateOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_couple(result.couple), status_code=HTTPStatus.CREATED)


async def list_couples_handler(request: Request) -> Response:
    include_archived = request.query_params.get("include_archived") == "true"
    result = get_couples(include_archived=include_archived)
    return JSONResponse([serialize_couple(c) for c in result.couples])


async def update_couple_handler(request: Request) -> Response:
    couple_id = request.path_params["id"]
    user_id = request.state.user_id
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    member_ids = body.get("member_ids")
    started_at = body.get("started_at")
    relationship_status = body.get("relationship_status")
    status = body.get("status")
    if member_ids is not None and not isinstance(member_ids, list):
        return bad_request("member_ids must be a list.")
    if started_at is not None and not isinstance(started_at, str):
        return bad_request("started_at must be a string.")

    result = update_couple(
        couple_id,
        viewer_user_id=user_id,
        member_ids=member_ids,
        started_at=started_at,
        relationship_status=relationship_status,
        status=status,
    )
    if result.status is not DateOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_couple(result.couple))


async def delete_couple_handler(request: Request) -> Response:
    couple_id = request.path_params["id"]
    result = delete_couple(couple_id)
    if result.status is not DateOperationStatus.OK:
        return error_response(result.status)
    return Response(status_code=HTTPStatus.NO_CONTENT)


# Events
async def create_event_handler(request: Request) -> Response:
    user_id = request.state.user_id
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    couple_id = body.get("couple_id")
    week_start = body.get("week_start")
    if not isinstance(couple_id, int) or isinstance(couple_id, bool):
        return bad_request("couple_id is required.")
    if not isinstance(week_start, str):
        return bad_request("week_start is required.")

    result = create_event(
        couple_id=couple_id,
        week_start=week_start,
        viewer_user_id=user_id,
        planned_by=body.get("planned_by"),
        title=body.get("title"),
        scheduled_date=body.get("scheduled_date"),
        scheduled_time=body.get("scheduled_time"),
        attributes=body.get("attributes"),
    )
    if result.status is not DateOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_event(result.event), status_code=HTTPStatus.CREATED)


async def list_events_handler(request: Request) -> Response:
    user_id = request.state.user_id
    couple_id = parse_int_param(request.query_params.get("couple_id"))
    if couple_id is False:
        return bad_request("couple_id must be an integer.")
    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")
    result = list_events(
        viewer_user_id=user_id,
        couple_id=couple_id,
        from_date=from_date,
        to_date=to_date,
    )
    if result.status is not DateOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse([serialize_event(e) for e in result.events])


async def get_event_detail_handler(request: Request) -> Response:
    user_id = request.state.user_id
    event_id = request.path_params["id"]
    result = get_event_detail(event_id, user_id)
    if result.status is not DateOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_event(result.event))


async def update_event_handler(request: Request) -> Response:
    user_id = request.state.user_id
    event_id = request.path_params["id"]
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    result = update_event(
        event_id=event_id,
        viewer_user_id=user_id,
        planned_by=body.get("planned_by"),
        scheduled_date=body.get("scheduled_date"),
        scheduled_time=body.get("scheduled_time"),
        title=body.get("title"),
        attributes=body.get("attributes"),
    )
    if result.status is not DateOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_event(result.event))


async def complete_event_handler(request: Request) -> Response:
    user_id = request.state.user_id
    event_id = request.path_params["id"]
    result = complete_event(event_id, user_id)
    if result.status is not DateOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_event(result.event))


async def delete_event_handler(request: Request) -> Response:
    user_id = request.state.user_id
    event_id = request.path_params["id"]
    result = delete_event(event_id, user_id)
    if result.status is not DateOperationStatus.OK:
        return error_response(result.status)
    return Response(status_code=HTTPStatus.NO_CONTENT)


# Memories
async def add_memory_handler(request: Request) -> Response:
    user_id = request.state.user_id
    event_id = request.path_params["id"]
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    kind = body.get("kind")
    result = add_memory(
        event_id=event_id,
        viewer_user_id=user_id,
        kind=kind,
        media_url=body.get("media_url"),
        caption=body.get("caption"),
        taken_by=body.get("taken_by"),
    )
    if result.status is not DateOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_memory(result.memory), status_code=HTTPStatus.CREATED)


async def list_memories_handler(request: Request) -> Response:
    user_id = request.state.user_id
    event_id = request.path_params["id"]
    result = list_memories(event_id, user_id)
    if result.status is not DateOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse([serialize_memory(m) for m in result.memories])


async def delete_memory_handler(request: Request) -> Response:
    user_id = request.state.user_id
    memory_id = request.path_params["id"]
    result = delete_memory(memory_id, user_id)
    if result.status is not DateOperationStatus.OK:
        return error_response(result.status)
    return Response(status_code=HTTPStatus.NO_CONTENT)


# Milestones
async def create_milestone_handler(request: Request) -> Response:
    user_id = request.state.user_id
    couple_id = request.path_params["id"]
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    milestone_type = body.get("type")
    date = body.get("date")
    label = body.get("label")
    if not isinstance(milestone_type, str):
        return bad_request("type is required.")
    if not isinstance(date, str):
        return bad_request("date is required.")
    if not isinstance(label, str):
        return bad_request("label is required.")

    result = create_milestone(
        couple_id,
        user_id,
        milestone_type=milestone_type,
        date=date,
        label=label,
        notes=body.get("notes"),
    )
    if result.status is not DateOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_milestone(result.milestone), status_code=HTTPStatus.CREATED)


async def list_milestones_handler(request: Request) -> Response:
    user_id = request.state.user_id
    couple_id = request.path_params["id"]
    result = list_milestones(couple_id, user_id)
    if result.status is not DateOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse([serialize_milestone(m) for m in result.milestones])


async def delete_milestone_handler(request: Request) -> Response:
    user_id = request.state.user_id
    milestone_id = request.path_params["id"]
    result = delete_milestone(milestone_id, user_id)
    if result.status is not DateOperationStatus.OK:
        return error_response(result.status)
    return Response(status_code=HTTPStatus.NO_CONTENT)
