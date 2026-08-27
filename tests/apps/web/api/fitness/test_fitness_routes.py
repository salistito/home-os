import json
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.requests import Request

from apps.web.api.fitness.routes import (
    create_exercise_handler,
    delete_exercise_entry_handler,
    delete_exercise_handler,
    delete_weight_handler,
    get_stats_handler,
    list_exercise_entries_handler,
    list_exercises_handler,
    list_weight_handler,
    log_exercise_handler,
    log_weight_handler,
    update_exercise_entry_handler,
    update_exercise_handler,
    update_weight_handler,
)
from modules.fitness.types import (
    Exercise,
    ExerciseEntry,
    FitnessOperationResult,
    FitnessOperationStatus,
    FitnessStats,
    WeightEntry,
)


@pytest.fixture
def mock_request():
    req = MagicMock(spec=Request)
    req.path_params = {}
    req.query_params = {}
    req.json = AsyncMock()
    req.state = MagicMock()
    req.state.user_id = 1
    return req


_D = "2026-03-15"
_WEIGHT = WeightEntry(1, 1, 80.5, None, _D, _D)
_ENTRY = ExerciseEntry(1, 1, 3, None, 45, 450.0, [], {}, None, _D, _D)
_CATALOG = Exercise(3, "Sentadilla", "piernas", _D, _D, None)
_NAMES = {3: "Sentadilla"}


# -- Weight --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_weight_success(mock_request):
    mock_request.json.return_value = {"weight_kg": 80.5}
    result = FitnessOperationResult(weight_entry=_WEIGHT)

    with patch("apps.web.api.fitness.routes.log_weight", return_value=result):
        resp = await log_weight_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED
    body = json.loads(resp.body)
    assert body["weight_kg"] == 80.5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_weight_invalid_json(mock_request):
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await log_weight_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_weight_body_not_dict(mock_request):
    mock_request.json.return_value = [1]

    resp = await log_weight_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_weight_service_error(mock_request):
    mock_request.json.return_value = {"weight_kg": -1}
    result = FitnessOperationResult(status=FitnessOperationStatus.INVALID_WEIGHT)

    with patch("apps.web.api.fitness.routes.log_weight", return_value=result):
        resp = await log_weight_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    body = json.loads(resp.body)
    assert body["error"] == "invalid_weight"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_weight(mock_request):
    mock_request.query_params = {"from_date": "2026-03-01"}

    with patch(
        "apps.web.api.fitness.routes.list_weight_entries", return_value=[_WEIGHT]
    ) as mock_list:
        resp = await list_weight_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert len(body) == 1
    mock_list.assert_called_once_with(1, "2026-03-01", None)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_weight_success(mock_request):
    mock_request.path_params["id"] = 1
    result = FitnessOperationResult(weight_entry=_WEIGHT)

    with patch("apps.web.api.fitness.routes.delete_weight_entry", return_value=result):
        resp = await delete_weight_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_weight_not_found(mock_request):
    mock_request.path_params["id"] = 99
    result = FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    with patch("apps.web.api.fitness.routes.delete_weight_entry", return_value=result):
        resp = await delete_weight_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_weight_success(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = {"weight_kg": 79.2, "notes": "ayuno"}
    result = FitnessOperationResult(weight_entry=_WEIGHT)

    with patch(
        "apps.web.api.fitness.routes.update_weight_entry", return_value=result
    ) as mock_update:
        resp = await update_weight_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert body["weight_kg"] == 80.5
    mock_update.assert_called_once_with(1, 1, weight_kg=79.2, notes="ayuno")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_weight_invalid_json(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await update_weight_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_weight_body_not_dict(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = [1]

    resp = await update_weight_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_weight_no_fields(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = {}

    resp = await update_weight_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    body = json.loads(resp.body)
    assert body["error"] == "invalid_request"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_weight_service_error(mock_request):
    mock_request.path_params["id"] = 99
    mock_request.json.return_value = {"weight_kg": 80}
    result = FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    with patch("apps.web.api.fitness.routes.update_weight_entry", return_value=result):
        resp = await update_weight_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_weight_duplicate_date_conflict(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = {"measured_at": _D}
    result = FitnessOperationResult(status=FitnessOperationStatus.DUPLICATE_DATE)

    with patch("apps.web.api.fitness.routes.update_weight_entry", return_value=result):
        resp = await update_weight_handler(mock_request)

    assert resp.status_code == HTTPStatus.CONFLICT
    body = json.loads(resp.body)
    assert body["error"] == "duplicate_date"


# -- Catalog --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_catalog_success(mock_request):
    mock_request.json.return_value = {"name": " Sentadilla ", "kind": "piernas"}
    result = FitnessOperationResult(exercise=_CATALOG)

    with patch("apps.web.api.fitness.routes.create_exercise", return_value=result) as mock_create:
        resp = await create_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED
    body = json.loads(resp.body)
    assert body["name"] == "Sentadilla"
    assert body["kind"] == "piernas"
    mock_create.assert_called_once_with(" Sentadilla ", "piernas")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_catalog_invalid_json(mock_request):
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await create_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_catalog_body_not_dict(mock_request):
    mock_request.json.return_value = "nope"

    resp = await create_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_catalog_invalid_kind(mock_request):
    mock_request.json.return_value = {"name": "Sentadilla", "kind": "x" * 41}
    result = FitnessOperationResult(status=FitnessOperationStatus.INVALID_KIND)

    with patch("apps.web.api.fitness.routes.create_exercise", return_value=result):
        resp = await create_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    body = json.loads(resp.body)
    assert body["error"] == "invalid_kind"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_catalog_duplicate(mock_request):
    mock_request.json.return_value = {"name": "Sentadilla"}
    result = FitnessOperationResult(status=FitnessOperationStatus.DUPLICATE_NAME)

    with patch("apps.web.api.fitness.routes.create_exercise", return_value=result):
        resp = await create_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.CONFLICT
    body = json.loads(resp.body)
    assert body["error"] == "duplicate_name"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_catalog(mock_request):
    with patch("apps.web.api.fitness.routes.list_exercises", return_value=[_CATALOG]) as mock_list:
        resp = await list_exercises_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert len(body) == 1
    assert body[0]["name"] == "Sentadilla"
    mock_list.assert_called_once_with()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_catalog_success(mock_request):
    mock_request.path_params["id"] = 3
    mock_request.json.return_value = {"name": " Peso muerto ", "kind": None}

    updated = Exercise(3, "Peso muerto", None, _D, _D, None)
    result = FitnessOperationResult(exercise=updated)
    with patch("apps.web.api.fitness.routes.update_exercise", return_value=result) as mock_update:
        resp = await update_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert body["name"] == "Peso muerto"
    assert body["kind"] is None
    mock_update.assert_called_once_with(3, name=" Peso muerto ", kind=None)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_catalog_no_fields(mock_request):
    mock_request.path_params["id"] = 3
    mock_request.json.return_value = {}

    resp = await update_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_catalog_body_not_dict(mock_request):
    mock_request.path_params["id"] = 3
    mock_request.json.return_value = ["not", "a", "dict"]

    resp = await update_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_catalog_ignores_unknown_fields(mock_request):
    mock_request.path_params["id"] = 3
    mock_request.json.return_value = {"hacker": True}

    resp = await update_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_catalog_invalid_json(mock_request):
    mock_request.path_params["id"] = 3
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await update_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_catalog_not_found(mock_request):
    mock_request.path_params["id"] = 99
    mock_request.json.return_value = {"name": "X"}
    result = FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    with patch("apps.web.api.fitness.routes.update_exercise", return_value=result):
        resp = await update_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_catalog_success(mock_request):
    mock_request.path_params["id"] = 3
    result = FitnessOperationResult(exercise=_CATALOG)

    with patch("apps.web.api.fitness.routes.delete_exercise", return_value=result):
        resp = await delete_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert body["name"] == "Sentadilla"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_catalog_not_found(mock_request):
    mock_request.path_params["id"] = 99
    result = FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    with patch("apps.web.api.fitness.routes.delete_exercise", return_value=result):
        resp = await delete_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


# -- Exercise Entries --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_exercise_success(mock_request):
    mock_request.json.return_value = {"exercise_id": 3, "duration_min": 45}
    result = FitnessOperationResult(exercise_entry=_ENTRY)

    with (
        patch("apps.web.api.fitness.routes.log_exercise", return_value=result),
        patch("apps.web.api.fitness.routes.get_exercise_name_map", return_value=_NAMES),
        patch("apps.web.api.fitness.routes.get_routine_name_map", return_value={}),
    ):
        resp = await log_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED
    body = json.loads(resp.body)
    assert body["exercise_name"] == "Sentadilla"
    assert body["duration_min"] == 45
    assert body["sets_breakdown"] == []
    assert body["volume_kg"] is None
    assert body["total_reps"] is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_exercise_with_sets_returns_derived_volume(mock_request):
    sets_rows = [{"name": "press", "weight_kg": 50.0, "reps": 8, "sets": 3}]
    entry_with_sets = ExerciseEntry(1, 1, 3, None, 60, None, sets_rows, {}, None, _D, _D)
    mock_request.json.return_value = {
        "exercise_id": 3,
        "duration_min": 60,
        "sets_breakdown": [{"name": "press", "weight_kg": 50, "reps": 8, "sets": 3}],
    }
    result = FitnessOperationResult(exercise_entry=entry_with_sets)

    with (
        patch("apps.web.api.fitness.routes.log_exercise", return_value=result),
        patch("apps.web.api.fitness.routes.get_exercise_name_map", return_value=_NAMES),
        patch("apps.web.api.fitness.routes.get_routine_name_map", return_value={}),
    ):
        resp = await log_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED
    body = json.loads(resp.body)
    assert body["sets_breakdown"] == sets_rows
    assert body["volume_kg"] == 1200.0
    assert body["total_reps"] == 24


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_exercise_invalid_sets(mock_request):
    mock_request.json.return_value = {
        "exercise_id": 3,
        "duration_min": 30,
        "sets_breakdown": [{"weight_kg": -1, "reps": 8}],
    }
    result = FitnessOperationResult(status=FitnessOperationStatus.INVALID_SETS_BREAKDOWN)

    with patch("apps.web.api.fitness.routes.log_exercise", return_value=result):
        resp = await log_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    body = json.loads(resp.body)
    assert body["error"] == "invalid_sets_breakdown"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_exercise_invalid_json(mock_request):
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await log_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_exercise_body_not_dict(mock_request):
    mock_request.json.return_value = "nope"

    resp = await log_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_exercise_service_error(mock_request):
    mock_request.json.return_value = {"exercise_id": 3, "duration_min": 0}
    result = FitnessOperationResult(status=FitnessOperationStatus.INVALID_DURATION_MIN)

    with patch("apps.web.api.fitness.routes.log_exercise", return_value=result):
        resp = await log_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    body = json.loads(resp.body)
    assert body["error"] == "invalid_duration_min"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_entries_with_filters(mock_request):
    mock_request.query_params = {
        "exercise_id": "3",
        "from_date": "2026-03-01",
        "to_date": "2026-03-15",
        "limit": "5",
    }

    with (
        patch(
            "apps.web.api.fitness.routes.list_exercise_entries", return_value=[_ENTRY]
        ) as mock_list,
        patch("apps.web.api.fitness.routes.get_exercise_name_map", return_value=_NAMES),
        patch("apps.web.api.fitness.routes.get_routine_name_map", return_value={}),
    ):
        resp = await list_exercise_entries_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert len(body) == 1
    assert body[0]["exercise_name"] == "Sentadilla"
    mock_list.assert_called_once_with(1, 3, "2026-03-01", "2026-03-15", 5)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_entries_invalid_exercise_id(mock_request):
    mock_request.query_params = {"exercise_id": "abc"}

    resp = await list_exercise_entries_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_entries_invalid_limit(mock_request):
    mock_request.query_params = {"limit": "abc"}

    resp = await list_exercise_entries_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_entries_without_filters(mock_request):
    with (
        patch("apps.web.api.fitness.routes.list_exercise_entries", return_value=[]) as mock_list,
        patch("apps.web.api.fitness.routes.get_exercise_name_map", return_value={}),
        patch("apps.web.api.fitness.routes.get_routine_name_map", return_value={}),
    ):
        resp = await list_exercise_entries_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    assert json.loads(resp.body) == []
    mock_list.assert_called_once_with(1, None, None, None, None)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_entry_success(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = {"duration_min": 60, "notes": "hoy"}

    updated = ExerciseEntry(1, 1, 3, None, 60, None, [], {}, "hoy", _D, _D)
    result = FitnessOperationResult(exercise_entry=updated)
    with (
        patch("apps.web.api.fitness.routes.update_exercise_entry", return_value=result),
        patch("apps.web.api.fitness.routes.get_exercise_name_map", return_value=_NAMES),
        patch("apps.web.api.fitness.routes.get_routine_name_map", return_value={}),
    ):
        resp = await update_exercise_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert body["notes"] == "hoy"
    assert body["exercise_name"] == "Sentadilla"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_entry_no_fields(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = {}

    resp = await update_exercise_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_entry_body_not_dict(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = ["nope"]

    resp = await update_exercise_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_entry_invalid_json(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await update_exercise_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_entry_not_found(mock_request):
    mock_request.path_params["id"] = 99
    mock_request.json.return_value = {"notes": "x"}
    result = FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    with patch("apps.web.api.fitness.routes.update_exercise_entry", return_value=result):
        resp = await update_exercise_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_entry_success(mock_request):
    mock_request.path_params["id"] = 1
    result = FitnessOperationResult(exercise_entry=_ENTRY)

    with (
        patch("apps.web.api.fitness.routes.delete_exercise_entry", return_value=result),
        patch("apps.web.api.fitness.routes.get_exercise_name_map", return_value=_NAMES),
        patch("apps.web.api.fitness.routes.get_routine_name_map", return_value={}),
    ):
        resp = await delete_exercise_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert body["exercise_name"] == "Sentadilla"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_entry_not_found(mock_request):
    mock_request.path_params["id"] = 99
    result = FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    with patch("apps.web.api.fitness.routes.delete_exercise_entry", return_value=result):
        resp = await delete_exercise_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


# -- Stats --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_stats(mock_request):
    stats = FitnessStats(latest_weight_kg=78.0, minutes_last_7d=90, sessions_last_7d=2)

    with patch("apps.web.api.fitness.routes.get_fitness_stats", return_value=stats):
        resp = await get_stats_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert body["latest_weight_kg"] == 78.0
    assert body["minutes_last_7d"] == 90
