import json
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.requests import Request

from apps.web.api.fitness.routes import (
    create_exercise_handler,
    delete_exercise_handler,
    delete_weight_handler,
    get_stats_handler,
    list_exercises_handler,
    list_weight_handler,
    log_weight_handler,
    update_exercise_handler,
)
from modules.fitness.types import (
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


_WEIGHT = WeightEntry(1, 1, 80.5, "2026-03-15", None, "2026-03-15")
_EXERCISE = ExerciseEntry(1, 1, "correr", 45, "high", 450.0, "2026-03-15", None, "2026-03-15")


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


# -- Exercises --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_exercise_success(mock_request):
    mock_request.json.return_value = {
        "exercise_type": "correr",
        "duration_min": 45,
        "intensity": "high",
    }
    result = FitnessOperationResult(exercise_entry=_EXERCISE)

    with patch("apps.web.api.fitness.routes.create_exercise", return_value=result) as mock_create:
        resp = await create_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED
    body = json.loads(resp.body)
    assert body["exercise_type"] == "correr"
    assert body["intensity"] == "high"
    mock_create.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_exercise_invalid_json(mock_request):
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await create_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_exercise_body_not_dict(mock_request):
    mock_request.json.return_value = "nope"

    resp = await create_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_exercise_service_error(mock_request):
    mock_request.json.return_value = {"exercise_type": "x", "duration_min": 0}
    result = FitnessOperationResult(status=FitnessOperationStatus.INVALID_DURATION)

    with patch("apps.web.api.fitness.routes.create_exercise", return_value=result):
        resp = await create_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_exercises_with_filters(mock_request):
    mock_request.query_params = {"type": "correr", "limit": "5"}

    with patch(
        "apps.web.api.fitness.routes.list_exercises", return_value=[_EXERCISE]
    ) as mock_list:
        resp = await list_exercises_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert len(body) == 1
    mock_list.assert_called_once_with(1, "correr", None, None, 5)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_exercises_invalid_limit(mock_request):
    mock_request.query_params = {"limit": "abc"}

    resp = await list_exercises_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_exercise_success(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = {"duration_min": 60}

    result = FitnessOperationResult(exercise_entry=_EXERCISE)
    with patch("apps.web.api.fitness.routes.update_exercise", return_value=result):
        resp = await update_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_exercise_no_fields(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = {}

    resp = await update_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_exercise_ignores_unknown_fields(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = {"hacker": True}

    resp = await update_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_exercise_invalid_json(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await update_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_exercise_not_found(mock_request):
    mock_request.path_params["id"] = 99
    mock_request.json.return_value = {"notes": "x"}
    result = FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    with patch("apps.web.api.fitness.routes.update_exercise", return_value=result):
        resp = await update_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_exercise_success(mock_request):
    mock_request.path_params["id"] = 1
    result = FitnessOperationResult(exercise_entry=_EXERCISE)

    with patch("apps.web.api.fitness.routes.delete_exercise", return_value=result):
        resp = await delete_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_exercise_not_found(mock_request):
    mock_request.path_params["id"] = 99
    result = FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    with patch("apps.web.api.fitness.routes.delete_exercise", return_value=result):
        resp = await delete_exercise_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


# -- Stats --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_stats(mock_request):
    stats = FitnessStats(latest_weight_kg=78.0, minutes_last_7d=90, sessions_last_7d=2)

    with patch("apps.web.api.fitness.routes.get_stats", return_value=stats):
        resp = await get_stats_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert body["latest_weight_kg"] == 78.0
    assert body["minutes_last_7d"] == 90
