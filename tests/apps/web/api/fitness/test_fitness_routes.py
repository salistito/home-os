import json
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.requests import Request

from apps.web.api.fitness.routes import (
    create_exercise_handler,
    create_routine_handler,
    delete_exercise_handler,
    delete_routine_handler,
    delete_weight_handler,
    delete_workout_entry_handler,
    get_routine_handler,
    get_stats_handler,
    list_exercises_handler,
    list_routines_handler,
    list_weight_handler,
    list_workout_entries_handler,
    log_weight_handler,
    log_workout_handler,
    replace_routine_exercises_handler,
    update_exercise_handler,
    update_routine_handler,
    update_weight_handler,
    update_workout_entry_handler,
)
from modules.fitness.types import (
    Exercise,
    FitnessOperationResult,
    FitnessOperationStatus,
    FitnessStats,
    Routine,
    RoutineExercise,
    WeightEntry,
    WorkoutEntry,
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
_ENTRY = WorkoutEntry(1, 1, 3, None, 45, 450.0, [], {}, None, _D, _D)
_CATALOG = Exercise(3, "Sentadilla", "piernas", _D, _D, None)
_NAMES = {3: "Sentadilla"}
_ROUTINE = Routine(1, "Push day", "fuerza", "pecho y triceps", _D, _D, None)
_ROUTINE_EXERCISE = RoutineExercise(1, 1, 3, 50.0, 8, 3, 0)


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


# -- Workout Entries --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_workout_success(mock_request):
    mock_request.json.return_value = {"exercise_id": 3, "duration_min": 45}
    result = FitnessOperationResult(workout_entry=_ENTRY)

    with (
        patch("apps.web.api.fitness.routes.log_workout", return_value=result),
        patch("apps.web.api.fitness.routes.get_exercise_name_map", return_value=_NAMES),
        patch("apps.web.api.fitness.routes.get_routine_name_map", return_value={}),
    ):
        resp = await log_workout_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED
    body = json.loads(resp.body)
    assert body["exercise_name"] == "Sentadilla"
    assert body["duration_min"] == 45
    assert body["sets_breakdown"] == []
    assert body["volume_kg"] is None
    assert body["total_reps"] is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_workout_with_sets_returns_derived_volume(mock_request):
    sets_rows = [
        {"exercise_id": None, "exercise_name": "press", "weight_kg": 50.0, "reps": 8, "sets": 3}
    ]
    entry_with_sets = WorkoutEntry(1, 1, 3, None, 60, None, sets_rows, {}, None, _D, _D)
    mock_request.json.return_value = {
        "exercise_id": 3,
        "duration_min": 60,
        "sets_breakdown": [
            {"exercise_id": None, "exercise_name": "press", "weight_kg": 50, "reps": 8, "sets": 3}
        ],
    }
    result = FitnessOperationResult(workout_entry=entry_with_sets)

    with (
        patch("apps.web.api.fitness.routes.log_workout", return_value=result),
        patch("apps.web.api.fitness.routes.get_exercise_name_map", return_value=_NAMES),
        patch("apps.web.api.fitness.routes.get_routine_name_map", return_value={}),
    ):
        resp = await log_workout_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED
    body = json.loads(resp.body)
    assert body["sets_breakdown"] == sets_rows
    assert body["volume_kg"] == 1200.0
    assert body["total_reps"] == 24


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_workout_invalid_sets(mock_request):
    mock_request.json.return_value = {
        "exercise_id": 3,
        "duration_min": 30,
        "sets_breakdown": [{"weight_kg": -1, "reps": 8}],
    }
    result = FitnessOperationResult(status=FitnessOperationStatus.INVALID_SETS_BREAKDOWN)

    with patch("apps.web.api.fitness.routes.log_workout", return_value=result):
        resp = await log_workout_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    body = json.loads(resp.body)
    assert body["error"] == "invalid_sets_breakdown"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_workout_invalid_json(mock_request):
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await log_workout_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_workout_body_not_dict(mock_request):
    mock_request.json.return_value = "nope"

    resp = await log_workout_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_workout_service_error(mock_request):
    mock_request.json.return_value = {"exercise_id": 3, "duration_min": 0}
    result = FitnessOperationResult(status=FitnessOperationStatus.INVALID_DURATION_MIN)

    with patch("apps.web.api.fitness.routes.log_workout", return_value=result):
        resp = await log_workout_handler(mock_request)

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
            "apps.web.api.fitness.routes.list_workout_entries", return_value=[_ENTRY]
        ) as mock_list,
        patch("apps.web.api.fitness.routes.get_exercise_name_map", return_value=_NAMES),
        patch("apps.web.api.fitness.routes.get_routine_name_map", return_value={}),
    ):
        resp = await list_workout_entries_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert len(body) == 1
    assert body[0]["exercise_name"] == "Sentadilla"
    mock_list.assert_called_once_with(1, 3, "2026-03-01", "2026-03-15", 5)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_entries_invalid_exercise_id(mock_request):
    mock_request.query_params = {"exercise_id": "abc"}

    resp = await list_workout_entries_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_entries_invalid_limit(mock_request):
    mock_request.query_params = {"limit": "abc"}

    resp = await list_workout_entries_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_entries_without_filters(mock_request):
    with (
        patch("apps.web.api.fitness.routes.list_workout_entries", return_value=[]) as mock_list,
        patch("apps.web.api.fitness.routes.get_exercise_name_map", return_value={}),
        patch("apps.web.api.fitness.routes.get_routine_name_map", return_value={}),
    ):
        resp = await list_workout_entries_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    assert json.loads(resp.body) == []
    mock_list.assert_called_once_with(1, None, None, None, None)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_entry_success(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = {"duration_min": 60, "notes": "hoy"}

    updated = WorkoutEntry(1, 1, 3, None, 60, None, [], {}, "hoy", _D, _D)
    result = FitnessOperationResult(workout_entry=updated)
    with (
        patch("apps.web.api.fitness.routes.update_workout_entry", return_value=result),
        patch("apps.web.api.fitness.routes.get_exercise_name_map", return_value=_NAMES),
        patch("apps.web.api.fitness.routes.get_routine_name_map", return_value={}),
    ):
        resp = await update_workout_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert body["notes"] == "hoy"
    assert body["exercise_name"] == "Sentadilla"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_entry_no_fields(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = {}

    resp = await update_workout_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_entry_body_not_dict(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = ["nope"]

    resp = await update_workout_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_entry_invalid_json(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await update_workout_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_entry_not_found(mock_request):
    mock_request.path_params["id"] = 99
    mock_request.json.return_value = {"notes": "x"}
    result = FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    with patch("apps.web.api.fitness.routes.update_workout_entry", return_value=result):
        resp = await update_workout_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_entry_success(mock_request):
    mock_request.path_params["id"] = 1
    result = FitnessOperationResult(workout_entry=_ENTRY)

    with (
        patch("apps.web.api.fitness.routes.delete_workout_entry", return_value=result),
        patch("apps.web.api.fitness.routes.get_exercise_name_map", return_value=_NAMES),
        patch("apps.web.api.fitness.routes.get_routine_name_map", return_value={}),
    ):
        resp = await delete_workout_entry_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert body["exercise_name"] == "Sentadilla"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_entry_not_found(mock_request):
    mock_request.path_params["id"] = 99
    result = FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    with patch("apps.web.api.fitness.routes.delete_workout_entry", return_value=result):
        resp = await delete_workout_entry_handler(mock_request)

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


# -- Routines --


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_routine_success(mock_request):
    mock_request.json.return_value = {"name": " Push day ", "category": "fuerza", "exercises": []}
    result = FitnessOperationResult(routine=_ROUTINE, routine_exercises=[_ROUTINE_EXERCISE])

    with patch("apps.web.api.fitness.routes.create_routine", return_value=result) as mock_create:
        resp = await create_routine_handler(mock_request)

    assert resp.status_code == HTTPStatus.CREATED
    body = json.loads(resp.body)
    assert body["name"] == "Push day"
    assert body["exercises"][0]["exercise_id"] == 3
    mock_create.assert_called_once_with(
        name=" Push day ", category="fuerza", description=None, exercises=[]
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_routine_invalid_json(mock_request):
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await create_routine_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_routine_body_not_dict(mock_request):
    mock_request.json.return_value = "nope"

    resp = await create_routine_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_routine_service_error(mock_request):
    mock_request.json.return_value = {"name": "X"}
    result = FitnessOperationResult(status=FitnessOperationStatus.DUPLICATE_NAME)

    with patch("apps.web.api.fitness.routes.create_routine", return_value=result):
        resp = await create_routine_handler(mock_request)

    assert resp.status_code == HTTPStatus.CONFLICT


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_routine_success(mock_request):
    mock_request.path_params["id"] = 1
    result = FitnessOperationResult(routine=_ROUTINE, routine_exercises=[_ROUTINE_EXERCISE])

    with (
        patch("apps.web.api.fitness.routes.get_routine_details", return_value=result),
        patch("apps.web.api.fitness.routes.get_exercise_name_map", return_value=_NAMES),
    ):
        resp = await get_routine_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert body["name"] == "Push day"
    assert body["exercises"][0]["exercise_name"] == "Sentadilla"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_routine_not_found(mock_request):
    mock_request.path_params["id"] = 99
    result = FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    with patch("apps.web.api.fitness.routes.get_routine_details", return_value=result):
        resp = await get_routine_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_routines_success(mock_request):
    details = FitnessOperationResult(routine=_ROUTINE, routine_exercises=[_ROUTINE_EXERCISE])

    with (
        patch("apps.web.api.fitness.routes.list_routines", return_value=[_ROUTINE]),
        patch("apps.web.api.fitness.routes.get_exercise_name_map", return_value=_NAMES),
        patch("apps.web.api.fitness.routes.get_routine_details", return_value=details),
    ):
        resp = await list_routines_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert len(body) == 1
    assert body[0]["name"] == "Push day"
    assert body[0]["exercises"][0]["exercise_name"] == "Sentadilla"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_routine_success(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = {"name": " Pull day ", "category": None}
    result = FitnessOperationResult(routine=_ROUTINE)

    with patch("apps.web.api.fitness.routes.update_routine", return_value=result) as mock_update:
        resp = await update_routine_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert body["name"] == "Push day"
    mock_update.assert_called_once_with(1, name=" Pull day ", category=None)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_routine_no_fields(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = {}

    resp = await update_routine_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_routine_invalid_json(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await update_routine_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_routine_body_not_dict(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = ["nope"]

    resp = await update_routine_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_routine_not_found(mock_request):
    mock_request.path_params["id"] = 99
    mock_request.json.return_value = {"name": "X"}
    result = FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    with patch("apps.web.api.fitness.routes.update_routine", return_value=result):
        resp = await update_routine_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
async def test_replace_routine_exercises_success(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = {"exercises": [{"exercise_id": 3, "reps": 8}]}
    result = FitnessOperationResult(routine=_ROUTINE, routine_exercises=[_ROUTINE_EXERCISE])

    with (
        patch("apps.web.api.fitness.routes.replace_routine_exercises", return_value=result),
        patch("apps.web.api.fitness.routes.get_exercise_name_map", return_value=_NAMES),
    ):
        resp = await replace_routine_exercises_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert body["name"] == "Push day"
    assert body["exercises"][0]["exercise_name"] == "Sentadilla"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_replace_routine_exercises_missing_field(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = {}

    resp = await replace_routine_exercises_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_replace_routine_exercises_invalid_json(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

    resp = await replace_routine_exercises_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_replace_routine_exercises_body_not_dict(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = ["nope"]

    resp = await replace_routine_exercises_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_replace_routine_exercises_service_error(mock_request):
    mock_request.path_params["id"] = 1
    mock_request.json.return_value = {"exercises": [{"exercise_id": 0}]}
    result = FitnessOperationResult(status=FitnessOperationStatus.INVALID_ROUTINE_EXERCISES)

    with patch("apps.web.api.fitness.routes.replace_routine_exercises", return_value=result):
        resp = await replace_routine_exercises_handler(mock_request)

    assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_routine_success(mock_request):
    mock_request.path_params["id"] = 1
    result = FitnessOperationResult(routine=_ROUTINE)

    with patch("apps.web.api.fitness.routes.delete_routine", return_value=result):
        resp = await delete_routine_handler(mock_request)

    assert resp.status_code == HTTPStatus.OK
    body = json.loads(resp.body)
    assert body["name"] == "Push day"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_routine_not_found(mock_request):
    mock_request.path_params["id"] = 99
    result = FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    with patch("apps.web.api.fitness.routes.delete_routine", return_value=result):
        resp = await delete_routine_handler(mock_request)

    assert resp.status_code == HTTPStatus.NOT_FOUND
