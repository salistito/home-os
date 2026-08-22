from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from modules.fitness.service import (
    create_exercise,
    delete_exercise,
    delete_weight_entry,
    get_stats,
    list_exercises,
    list_weight_entries,
    log_weight,
    update_exercise,
)
from modules.fitness.types import (
    ExerciseEntry,
    FitnessOperationStatus,
    WeightEntry,
)

_TODAY = date(2026, 3, 15)
_D = "2026-03-15"

_WEIGHT = WeightEntry(1, 1, 80.5, _D, None, _D)
_EXERCISE = ExerciseEntry(1, 1, "correr", 45, "high", 450.0, _D, None, _D)


def _mock_today():
    return _TODAY


@pytest.fixture
def patched_today():
    with patch("modules.fitness.service.get_today", _mock_today):
        yield


# -- log_weight --


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_log_weight_defaults_to_today(mock_repo):
    mock_repo.upsert_weight_entry.return_value = _WEIGHT

    result = log_weight(1, 80.5)

    assert result.status == FitnessOperationStatus.OK
    assert result.weight_entry.weight_kg == 80.5
    mock_repo.upsert_weight_entry.assert_called_once_with(
        user_id=1, weight_kg=80.5, measured_at=_D, notes=None, created_at=_D
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_log_weight_with_explicit_date_and_notes(mock_repo):
    mock_repo.upsert_weight_entry.return_value = _WEIGHT

    result = log_weight(1, 79.321, measured_at="2026-03-14", notes="  ayuno  ")

    assert result.status == FitnessOperationStatus.OK
    mock_repo.upsert_weight_entry.assert_called_once_with(
        user_id=1, weight_kg=79.32, measured_at="2026-03-14", notes="ayuno", created_at=_D
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "weight",
    [None, "80", True, 0, -1, 501, float("nan") if False else []],
)
@patch("modules.fitness.service.repository")
def test_log_weight_invalid_values(mock_repo, weight):
    result = log_weight(1, weight)
    assert result.status == FitnessOperationStatus.INVALID_WEIGHT
    mock_repo.upsert_weight_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_log_weight_invalid_measured_at(mock_repo):
    result = log_weight(1, 80.0, measured_at="15/03/2026")
    assert result.status == FitnessOperationStatus.INVALID_MEASURED_AT
    mock_repo.upsert_weight_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_list_weight_entries_passthrough(mock_repo):
    mock_repo.get_weight_entries.return_value = [_WEIGHT]
    entries = list_weight_entries(1, "2026-03-01", "2026-03-15")
    assert entries == [_WEIGHT]
    mock_repo.get_weight_entries.assert_called_once_with(1, "2026-03-01", "2026-03-15")


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_delete_weight_entry_ok(mock_repo):
    mock_repo.get_weight_entry_by_id_and_user.return_value = _WEIGHT
    result = delete_weight_entry(1, 1)
    assert result.status == FitnessOperationStatus.OK
    mock_repo.delete_weight_entry.assert_called_once_with(1, 1)


@pytest.mark.unit
@pytest.mark.parametrize("entry_id", [None, "x", 0, -5])
def test_delete_weight_entry_invalid_id(entry_id):
    assert delete_weight_entry(entry_id, 1).status == FitnessOperationStatus.INVALID_ID


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_delete_weight_entry_not_found(mock_repo):
    mock_repo.get_weight_entry_by_id_and_user.return_value = None
    assert delete_weight_entry(99, 1).status == FitnessOperationStatus.NOT_FOUND


# -- create_exercise --


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_create_exercise_full(mock_repo):
    mock_repo.create_exercise_entry.return_value = _EXERCISE

    result = create_exercise(
        1,
        "  Correr  ",
        45,
        intensity="high",
        calories_burned=450.44,
        performed_at="2026-03-14",
        notes="  5km  ",
    )

    assert result.status == FitnessOperationStatus.OK
    mock_repo.create_exercise_entry.assert_called_once_with(
        user_id=1,
        exercise_type="Correr",
        duration_min=45,
        intensity="high",
        calories_burned=450.4,
        performed_at="2026-03-14",
        notes="5km",
        created_at=_D,
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_create_exercise_defaults(mock_repo):
    entry = ExerciseEntry(2, 1, "yoga", 60, None, None, _D, None, _D)
    mock_repo.create_exercise_entry.return_value = entry

    result = create_exercise(1, "yoga", 60)

    assert result.status == FitnessOperationStatus.OK
    call_kwargs = mock_repo.create_exercise_entry.call_args.kwargs
    assert call_kwargs["performed_at"] == _D
    assert call_kwargs["intensity"] is None
    assert call_kwargs["calories_burned"] is None


@pytest.mark.unit
@pytest.mark.parametrize("exercise_type", [None, "", "   ", 42])
def test_create_exercise_invalid_type(exercise_type):
    assert (
        create_exercise(1, exercise_type, 30).status
        == FitnessOperationStatus.INVALID_EXERCISE_TYPE
    )


@pytest.mark.unit
@pytest.mark.parametrize("duration", [None, "30", True, 30.5, 0, -10, 1441])
def test_create_exercise_invalid_duration(duration):
    assert (
        create_exercise(1, "correr", duration).status
        == FitnessOperationStatus.INVALID_DURATION
    )


@pytest.mark.unit
@pytest.mark.parametrize("intensity", ["extreme", 3])
def test_create_exercise_invalid_intensity(intensity):
    assert (
        create_exercise(1, "correr", 30, intensity=intensity).status
        == FitnessOperationStatus.INVALID_INTENSITY
    )


@pytest.mark.unit
@pytest.mark.parametrize("calories", [-1, "300", True])
def test_create_exercise_invalid_calories(calories):
    assert (
        create_exercise(1, "correr", 30, calories_burned=calories).status
        == FitnessOperationStatus.INVALID_CALORIES
    )


@pytest.mark.unit
def test_create_exercise_invalid_performed_at():
    assert (
        create_exercise(1, "correr", 30, performed_at="bad").status
        == FitnessOperationStatus.INVALID_PERFORMED_AT
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_list_exercises_passthrough(mock_repo):
    mock_repo.get_exercise_entries.return_value = [_EXERCISE]
    entries = list_exercises(1, "correr", "2026-03-01", "2026-03-15", 10)
    assert entries == [_EXERCISE]
    mock_repo.get_exercise_entries.assert_called_once_with(
        1, "correr", "2026-03-01", "2026-03-15", 10
    )


# -- update_exercise --


@pytest.mark.unit
@pytest.mark.parametrize("entry_id", [None, "x", 0])
def test_update_exercise_invalid_id(entry_id):
    assert update_exercise(entry_id, 1).status == FitnessOperationStatus.INVALID_ID


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_exercise_not_found(mock_repo):
    mock_repo.get_exercise_entry_by_id_and_user.return_value = None
    assert update_exercise(99, 1).status == FitnessOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_exercise_no_fields_refetches(mock_repo):
    mock_repo.get_exercise_entry_by_id_and_user.side_effect = [_EXERCISE, _EXERCISE]

    result = update_exercise(1, 1)

    assert result.status == FitnessOperationStatus.OK
    mock_repo.update_exercise_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_exercise_all_fields(mock_repo):
    updated = ExerciseEntry(1, 1, "gym", 90, "medium", 500.0, "2026-03-16", "hoy", _D)
    mock_repo.get_exercise_entry_by_id_and_user.side_effect = [_EXERCISE, updated]

    result = update_exercise(
        1,
        1,
        exercise_type=" gym ",
        duration_min=90,
        intensity="medium",
        calories_burned=500.0,
        performed_at="2026-03-16",
        notes="hoy",
    )

    assert result.status == FitnessOperationStatus.OK
    assert result.exercise_entry.exercise_type == "gym"
    mock_repo.update_exercise_entry.assert_called_once_with(
        1,
        1,
        exercise_type="gym",
        duration_min=90,
        intensity="medium",
        calories_burned=500.0,
        performed_at="2026-03-16",
        notes="hoy",
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_exercise_clears_optional_fields(mock_repo):
    mock_repo.get_exercise_entry_by_id_and_user.side_effect = [_EXERCISE, _EXERCISE]

    result = update_exercise(1, 1, intensity=None, calories_burned=None, notes=None)

    assert result.status == FitnessOperationStatus.OK
    kwargs = mock_repo.update_exercise_entry.call_args.kwargs
    assert kwargs["intensity"] is None
    assert kwargs["calories_burned"] is None
    assert kwargs["notes"] is None


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_exercise_field_validation(mock_repo):
    cases = [
        {"exercise_type": ""},
        {"duration_min": "x"},
        {"intensity": "extreme"},
        {"calories_burned": -5},
        {"performed_at": "nope"},
    ]
    for fields in cases:
        mock_repo.get_exercise_entry_by_id_and_user.return_value = _EXERCISE
        result = update_exercise(1, 1, **fields)
        assert result.status != FitnessOperationStatus.OK, fields


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_exercise_row_missing_after_update(mock_repo):
    mock_repo.get_exercise_entry_by_id_and_user.return_value = _EXERCISE
    mock_repo.update_exercise_entry.return_value = False

    result = update_exercise(1, 1, notes="x")

    assert result.status == FitnessOperationStatus.NOT_FOUND


# -- delete_exercise --


@pytest.mark.unit
@pytest.mark.parametrize("entry_id", [None, "x", 0])
def test_delete_exercise_invalid_id(entry_id):
    assert delete_exercise(entry_id, 1).status == FitnessOperationStatus.INVALID_ID


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_delete_exercise_not_found(mock_repo):
    mock_repo.get_exercise_entry_by_id_and_user.return_value = None
    assert delete_exercise(99, 1).status == FitnessOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_delete_exercise_ok(mock_repo):
    mock_repo.get_exercise_entry_by_id_and_user.return_value = _EXERCISE

    result = delete_exercise(1, 1)

    assert result.status == FitnessOperationStatus.OK
    mock_repo.delete_exercise_entry.assert_called_once_with(1, 1)


# -- get_stats --


@pytest.mark.unit
@patch("modules.fitness.service.get_today", _mock_today)
@patch("modules.fitness.service.repository")
def test_get_stats_full(mock_repo):
    latest = WeightEntry(1, 1, 78.0, "2026-03-15", None, _D)
    baseline_7d = WeightEntry(2, 1, 80.0, "2026-03-07", None, _D)
    baseline_30d = WeightEntry(3, 1, 82.0, "2026-02-20", None, _D)
    ex_7d = [
        ExerciseEntry(1, 1, "correr", 30, None, None, "2026-03-14", None, _D),
        ExerciseEntry(2, 1, "gym", 60, None, None, "2026-03-12", None, _D),
    ]
    ex_30d = ex_7d + [ExerciseEntry(3, 1, "yoga", 90, None, None, "2026-03-01", None, _D)]

    mock_repo.get_weight_entries.return_value = [latest]
    mock_repo.get_latest_weight_before.side_effect = [baseline_7d, baseline_30d]
    mock_repo.get_exercise_entries.side_effect = [ex_7d, ex_30d]

    stats = get_stats(1)

    assert stats.latest_weight_kg == 78.0
    assert stats.latest_measured_at == "2026-03-15"
    assert stats.weight_delta_7d == -2.0
    assert stats.weight_delta_30d == -4.0
    assert stats.minutes_last_7d == 90
    assert stats.sessions_last_7d == 2
    assert stats.minutes_last_30d == 180
    assert stats.sessions_last_30d == 3
    assert stats.by_type_last_30d == {"yoga": 90, "correr": 30, "gym": 60}


@pytest.mark.unit
@patch("modules.fitness.service.get_today", _mock_today)
@patch("modules.fitness.service.repository")
def test_get_stats_empty(mock_repo):
    mock_repo.get_weight_entries.return_value = []
    mock_repo.get_latest_weight_before.return_value = MagicMock()
    mock_repo.get_exercise_entries.return_value = []

    stats = get_stats(1)

    assert stats.latest_weight_kg is None
    assert stats.weight_delta_7d is None
    assert stats.weight_delta_30d is None
    assert stats.minutes_last_7d == 0
    assert stats.sessions_last_7d == 0
