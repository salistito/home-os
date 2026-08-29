import json
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.requests import Request

from apps.web.api.dates.routes import (
    add_memory_handler,
    complete_event_handler,
    create_couple_handler,
    create_event_handler,
    create_milestone_handler,
    delete_couple_handler,
    delete_event_handler,
    delete_memory_handler,
    delete_milestone_handler,
    get_event_detail_handler,
    list_couples_handler,
    list_events_handler,
    list_memories_handler,
    list_milestones_handler,
    update_couple_handler,
    update_event_handler,
)
from modules.dates.types import (
    DateCouple,
    DateEvent,
    DateMemory,
    DateMilestone,
    DateOperationResult,
    DateOperationStatus,
)

_D = "2026-03-15"
_COUPLE = DateCouple(1, [1, 2], _D, "couple", "active", _D, _D)
_EVENT = DateEvent(10, 1, "2026-03-16", 1, attributes=[])
_MEMORY = DateMemory(5, 10, "photo", "https://example.com/x.jpg")
_MILESTONE = DateMilestone(3, 1, "monthly", _D, "Cumple-mes", None, _D)


@pytest.fixture
def mock_request():
    req = MagicMock(spec=Request)
    req.path_params = {}
    req.query_params = {}
    req.json = AsyncMock()
    req.state = MagicMock()
    req.state.user_id = 1
    return req


# Couples


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_couple_success(mock_request):
    mock_request.json.return_value = {
        "member_ids": [1, 2],
        "started_at": "2026-03-15",
        "relationship_status": "married",
    }
    result = DateOperationResult(couple=_COUPLE)
    with patch("apps.web.api.dates.routes.create_couple", return_value=result) as m:
        resp = await create_couple_handler(mock_request)
    assert resp.status_code == HTTPStatus.CREATED
    m.assert_called_once_with(
        [1, 2], started_at="2026-03-15", relationship_status="married"
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_couple_missing_member_ids(mock_request):
    mock_request.json.return_value = {"started_at": "2026-03-15"}
    resp = await create_couple_handler(mock_request)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_couple_error(mock_request):
    mock_request.json.return_value = {"member_ids": [1]}
    result = DateOperationResult(status=DateOperationStatus.INVALID_STARTED_AT)
    with patch("apps.web.api.dates.routes.create_couple", return_value=result):
        resp = await create_couple_handler(mock_request)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_couples_active_only(mock_request):
    result = DateOperationResult(couples=[_COUPLE])
    with patch("apps.web.api.dates.routes.get_couples", return_value=result) as m:
        resp = await list_couples_handler(mock_request)
    assert resp.status_code == HTTPStatus.OK
    m.assert_called_once_with(include_archived=False)
    payload = json.loads(resp.body)
    assert payload[0]["member_ids"] == [1, 2]
    assert payload[0]["started_at"] == _D
    assert payload[0]["relationship_status"] == "couple"
    assert payload[0]["status"] == "active"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_couples_include_archived(mock_request):
    mock_request.query_params = {"include_archived": "true"}
    result = DateOperationResult(couples=[_COUPLE])
    with patch("apps.web.api.dates.routes.get_couples", return_value=result) as m:
        resp = await list_couples_handler(mock_request)
    assert resp.status_code == HTTPStatus.OK
    m.assert_called_once_with(include_archived=True)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_couple(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {
        "started_at": "2025-01-01",
        "relationship_status": "married",
        "status": "active",
    }
    result = DateOperationResult(couple=_COUPLE)
    with patch("apps.web.api.dates.routes.update_couple", return_value=result) as m:
        resp = await update_couple_handler(mock_request)
    assert resp.status_code == HTTPStatus.OK
    m.assert_called_once_with(
        1,
        viewer_user_id=1,
        member_ids=None,
        started_at="2025-01-01",
        relationship_status="married",
        status="active",
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_couple(mock_request):
    mock_request.path_params = {"id": 1}
    result = DateOperationResult()
    with patch("apps.web.api.dates.routes.delete_couple", return_value=result):
        resp = await delete_couple_handler(mock_request)
    assert resp.status_code == HTTPStatus.NO_CONTENT


# Milestones


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_milestone(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {
        "type": "anniversary",
        "date": "2026-03-15",
        "label": "Aniversario",
        "notes": "3 años",
    }
    result = DateOperationResult(milestone=_MILESTONE)
    with patch("apps.web.api.dates.routes.create_milestone", return_value=result) as m:
        resp = await create_milestone_handler(mock_request)
    assert resp.status_code == HTTPStatus.CREATED
    m.assert_called_once_with(
        1,
        1,
        milestone_type="anniversary",
        date="2026-03-15",
        label="Aniversario",
        notes="3 años",
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_milestone_missing_fields(mock_request):
    mock_request.path_params = {"id": 1}
    mock_request.json.return_value = {"type": "anniversary"}
    resp = await create_milestone_handler(mock_request)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_milestones(mock_request):
    mock_request.path_params = {"id": 1}
    result = DateOperationResult(milestones=[_MILESTONE])
    with patch("apps.web.api.dates.routes.list_milestones", return_value=result) as m:
        resp = await list_milestones_handler(mock_request)
    assert resp.status_code == HTTPStatus.OK
    m.assert_called_once_with(1, 1)
    payload = json.loads(resp.body)
    assert payload[0]["type"] == "monthly"
    assert payload[0]["label"] == "Cumple-mes"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_milestone(mock_request):
    mock_request.path_params = {"id": 3}
    result = DateOperationResult()
    with patch("apps.web.api.dates.routes.delete_milestone", return_value=result):
        resp = await delete_milestone_handler(mock_request)
    assert resp.status_code == HTTPStatus.NO_CONTENT


# Events


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_event_success(mock_request):
    mock_request.json.return_value = {
        "couple_id": 1,
        "week_start": "2026-03-16",
        "attributes": [{"key": "place", "value": "X"}],
    }
    result = DateOperationResult(event=_EVENT)
    with patch("apps.web.api.dates.routes.create_event", return_value=result) as m:
        resp = await create_event_handler(mock_request)
    assert resp.status_code == HTTPStatus.CREATED
    kwargs = m.call_args.kwargs
    assert kwargs["couple_id"] == 1
    assert kwargs["viewer_user_id"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_event_missing_fields(mock_request):
    mock_request.json.return_value = {"couple_id": 1}
    resp = await create_event_handler(mock_request)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_event_duplicate(mock_request):
    mock_request.json.return_value = {"couple_id": 1, "week_start": "2026-03-16"}
    result = DateOperationResult(status=DateOperationStatus.DUPLICATE_WEEK)
    with patch("apps.web.api.dates.routes.create_event", return_value=result):
        resp = await create_event_handler(mock_request)
    assert resp.status_code == HTTPStatus.CONFLICT


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_events(mock_request):
    mock_request.query_params = {"couple_id": "1", "from_date": "2026-03-01"}
    result = DateOperationResult(events=[_EVENT])
    with patch("apps.web.api.dates.routes.list_events", return_value=result) as m:
        resp = await list_events_handler(mock_request)
    assert resp.status_code == HTTPStatus.OK
    kwargs = m.call_args.kwargs
    assert kwargs["couple_id"] == 1
    assert kwargs["from_date"] == "2026-03-01"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_event_detail(mock_request):
    mock_request.path_params = {"id": 10}
    result = DateOperationResult(event=_EVENT)
    with patch("apps.web.api.dates.routes.get_event_detail", return_value=result):
        resp = await get_event_detail_handler(mock_request)
    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_event(mock_request):
    mock_request.path_params = {"id": 10}
    mock_request.json.return_value = {"scheduled_date": "2026-03-20"}
    result = DateOperationResult(event=_EVENT)
    with patch("apps.web.api.dates.routes.update_event", return_value=result) as m:
        resp = await update_event_handler(mock_request)
    assert resp.status_code == HTTPStatus.OK
    m.assert_called_once_with(
        event_id=10,
        viewer_user_id=1,
        planned_by=None,
        scheduled_date="2026-03-20",
        scheduled_time=None,
        title=None,
        attributes=None,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_complete_event(mock_request):
    mock_request.path_params = {"id": 10}
    result = DateOperationResult(event=_EVENT)
    with patch("apps.web.api.dates.routes.complete_event", return_value=result) as m:
        resp = await complete_event_handler(mock_request)
    assert resp.status_code == HTTPStatus.OK
    m.assert_called_once_with(10, 1)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_event(mock_request):
    mock_request.path_params = {"id": 10}
    result = DateOperationResult()
    with patch("apps.web.api.dates.routes.delete_event", return_value=result):
        resp = await delete_event_handler(mock_request)
    assert resp.status_code == HTTPStatus.NO_CONTENT


# Memories


@pytest.mark.unit
@pytest.mark.asyncio
async def test_add_memory(mock_request):
    mock_request.path_params = {"id": 10}
    mock_request.json.return_value = {"kind": "photo", "media_url": "https://example.com/x.jpg"}
    result = DateOperationResult(memory=_MEMORY)
    with patch("apps.web.api.dates.routes.add_memory", return_value=result) as m:
        resp = await add_memory_handler(mock_request)
    assert resp.status_code == HTTPStatus.CREATED
    m.assert_called_once_with(
        event_id=10,
        viewer_user_id=1,
        kind="photo",
        media_url="https://example.com/x.jpg",
        caption=None,
        taken_by=None,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_memories(mock_request):
    mock_request.path_params = {"id": 10}
    result = DateOperationResult(memories=[_MEMORY])
    with patch("apps.web.api.dates.routes.list_memories", return_value=result):
        resp = await list_memories_handler(mock_request)
    assert resp.status_code == HTTPStatus.OK
    payload = json.loads(resp.body)
    assert payload[0]["media_url"] == "https://example.com/x.jpg"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_memory(mock_request):
    mock_request.path_params = {"id": 5}
    result = DateOperationResult()
    with patch("apps.web.api.dates.routes.delete_memory", return_value=result):
        resp = await delete_memory_handler(mock_request)
    assert resp.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.unit
@pytest.mark.asyncio
async def test_error_response_maps_forbidden(mock_request):
    mock_request.path_params = {"id": 10}
    result = DateOperationResult(status=DateOperationStatus.FORBIDDEN)
    with patch("apps.web.api.dates.routes.get_event_detail", return_value=result):
        resp = await get_event_detail_handler(mock_request)
    assert resp.status_code == HTTPStatus.FORBIDDEN
