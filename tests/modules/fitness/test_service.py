from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from modules.fitness.errors import WeightEntryDateConflictError
from modules.fitness.service import (
    create_exercise,
    create_routine,
    delete_exercise,
    delete_routine,
    delete_weight_entry,
    delete_workout_entry,
    get_exercise_name_map,
    get_fitness_stats,
    get_routine_details,
    get_routine_name_map,
    list_exercises,
    list_routines,
    list_weight_entries,
    list_workout_entries,
    log_weight,
    log_workout,
    replace_routine_exercises,
    update_exercise,
    update_routine,
    update_weight_entry,
    update_workout_entry,
)
from modules.fitness.types import (
    Exercise,
    FitnessOperationStatus,
    Routine,
    RoutineExercise,
    WeightEntry,
    WorkoutEntry,
)

_TODAY = date(2026, 3, 15)
_D = "2026-03-15"

_WEIGHT = WeightEntry(1, 1, 80.5, None, _D, _D)
_ENTRY = WorkoutEntry(1, 1, 5, None, 45, 450.0, [], {}, None, _D, _D)
_CATALOG_EXERCISE = Exercise(3, "Sentadilla", "piernas", _D, _D, None)
_ROUTINE = Routine(1, "Push day", "fuerza", "pecho y triceps", _D, _D, None)
_ROUTINE_EXERCISE = RoutineExercise(1, 1, 3, 50.0, 8, 3, 0)


def _mock_today():
    return _TODAY


@pytest.fixture
def patched_today():
    with patch("modules.fitness.service.get_today", _mock_today):
        yield


# -- weight --


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
    [None, "80", True, 0, -1, 501],
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


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_weight_entry_ok(mock_repo):
    updated = WeightEntry(1, 1, 75.2, "post", "2026-03-14", _D)
    mock_repo.get_weight_entry_by_id_and_user.side_effect = [_WEIGHT, updated]
    mock_repo.get_weight_entry_by_user_and_date.return_value = None

    result = update_weight_entry(1, 1, weight_kg=75.234, notes=" post ", measured_at="2026-03-14")

    assert result.status == FitnessOperationStatus.OK
    assert result.weight_entry is updated
    mock_repo.update_weight_entry.assert_called_once_with(
        1, 1, weight_kg=75.23, measured_at="2026-03-14", notes="post"
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_weight_entry_no_fields_refetches(mock_repo):
    mock_repo.get_weight_entry_by_id_and_user.return_value = _WEIGHT

    result = update_weight_entry(1, 1)

    assert result.status == FitnessOperationStatus.OK
    assert result.weight_entry is _WEIGHT
    mock_repo.update_weight_entry.assert_not_called()


@pytest.mark.unit
@pytest.mark.parametrize("entry_id", [None, "x", 0, -5, True])
def test_update_weight_entry_invalid_id(entry_id):
    assert update_weight_entry(entry_id, 1).status == FitnessOperationStatus.INVALID_ID


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_weight_entry_not_found(mock_repo):
    mock_repo.get_weight_entry_by_id_and_user.return_value = None
    assert update_weight_entry(99, 1, weight_kg=80).status == (FitnessOperationStatus.NOT_FOUND)
    mock_repo.update_weight_entry.assert_not_called()


@pytest.mark.unit
@pytest.mark.parametrize("weight_kg", [None, "80", True, 0, -1, 501])
@patch("modules.fitness.service.repository")
def test_update_weight_entry_invalid_weight(mock_repo, weight_kg):
    mock_repo.get_weight_entry_by_id_and_user.return_value = _WEIGHT

    result = update_weight_entry(1, 1, weight_kg=weight_kg)

    assert result.status == FitnessOperationStatus.INVALID_WEIGHT
    mock_repo.update_weight_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_weight_entry_invalid_measured_at(mock_repo):
    mock_repo.get_weight_entry_by_id_and_user.return_value = _WEIGHT

    result = update_weight_entry(1, 1, measured_at="15/03/2026")

    assert result.status == FitnessOperationStatus.INVALID_MEASURED_AT
    mock_repo.get_weight_entry_by_user_and_date.assert_not_called()
    mock_repo.update_weight_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_weight_entry_duplicate_date(mock_repo):
    other = WeightEntry(2, 1, 70.0, None, "2026-03-14", _D)
    mock_repo.get_weight_entry_by_id_and_user.return_value = _WEIGHT
    mock_repo.get_weight_entry_by_user_and_date.return_value = other

    result = update_weight_entry(1, 1, measured_at="2026-03-14")

    assert result.status == FitnessOperationStatus.DUPLICATE_DATE
    mock_repo.update_weight_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_weight_entry_same_date_same_id_allowed(mock_repo):
    mock_repo.get_weight_entry_by_id_and_user.side_effect = [_WEIGHT, _WEIGHT]
    mock_repo.get_weight_entry_by_user_and_date.return_value = _WEIGHT

    result = update_weight_entry(1, 1, measured_at=_D)

    assert result.status == FitnessOperationStatus.OK
    mock_repo.update_weight_entry.assert_called_once_with(1, 1, measured_at=_D)


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_weight_entry_clears_notes(mock_repo):
    with_notes = WeightEntry(1, 1, 80.5, "ayuno", _D, _D)
    mock_repo.get_weight_entry_by_id_and_user.side_effect = [with_notes, _WEIGHT]

    result = update_weight_entry(1, 1, notes="   ")

    assert result.status == FitnessOperationStatus.OK
    mock_repo.update_weight_entry.assert_called_once_with(1, 1, notes=None)


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_weight_entry_row_missing_after_update(mock_repo):
    mock_repo.get_weight_entry_by_id_and_user.return_value = None

    result = update_weight_entry(1, 1, weight_kg=80)

    assert result.status == FitnessOperationStatus.NOT_FOUND


# -- catalog: create_exercise --


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_create_catalog_exercise_full(mock_repo):
    mock_repo.get_active_exercise_by_name.return_value = None
    mock_repo.create_exercise.return_value = _CATALOG_EXERCISE

    result = create_exercise("  Sentadilla  ", " piernas ")

    assert result.status == FitnessOperationStatus.OK
    assert result.exercise.name == "Sentadilla"
    mock_repo.create_exercise.assert_called_once_with(
        name="Sentadilla", kind="piernas", created_at=_D, updated_at=_D
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_create_catalog_exercise_defaults_kind(mock_repo):
    mock_repo.get_active_exercise_by_name.return_value = None
    mock_repo.create_exercise.return_value = _CATALOG_EXERCISE

    result = create_exercise("Press banca")

    assert result.status == FitnessOperationStatus.OK
    kwargs = mock_repo.create_exercise.call_args.kwargs
    assert kwargs["kind"] is None


@pytest.mark.unit
@pytest.mark.parametrize("name", [None, "", "   ", 42, "x" * 81])
def test_create_catalog_exercise_invalid_name(name):
    assert create_exercise(name).status == FitnessOperationStatus.INVALID_NAME


@pytest.mark.unit
@pytest.mark.parametrize("kind", ["x" * 41])
@patch("modules.fitness.service.repository")
def test_create_catalog_exercise_invalid_kind(mock_repo, kind):
    mock_repo.get_active_exercise_by_name.return_value = None
    assert create_exercise("Sentadilla", kind).status == FitnessOperationStatus.INVALID_KIND


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_create_catalog_exercise_blank_kind_normalizes_to_none(mock_repo):
    mock_repo.get_active_exercise_by_name.return_value = None
    mock_repo.create_exercise.return_value = _CATALOG_EXERCISE

    result = create_exercise("Sentadilla", "   ")

    assert result.status == FitnessOperationStatus.OK
    kwargs = mock_repo.create_exercise.call_args.kwargs
    assert kwargs["kind"] is None


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_create_catalog_exercise_duplicate_name(mock_repo):
    mock_repo.get_active_exercise_by_name.return_value = _CATALOG_EXERCISE

    result = create_exercise("Sentadilla")

    assert result.status == FitnessOperationStatus.DUPLICATE_NAME
    mock_repo.create_exercise.assert_not_called()


# -- catalog: list / map --


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_list_exercises_passthrough(mock_repo):
    mock_repo.get_exercises.return_value = [_CATALOG_EXERCISE]
    exercises = list_exercises()
    assert exercises == [_CATALOG_EXERCISE]
    mock_repo.get_exercises.assert_called_once_with(include_deleted=False)


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_get_exercise_name_map(mock_repo):
    other = Exercise(9, "Peso muerto", None, _D, _D, _D)
    mock_repo.get_exercises.return_value = [_CATALOG_EXERCISE, other]

    names = get_exercise_name_map()

    assert names == {3: "Sentadilla", 9: "Peso muerto"}
    mock_repo.get_exercises.assert_called_once_with(include_deleted=True)


# -- catalog: update_exercise --


@pytest.mark.unit
@pytest.mark.parametrize("exercise_id", [None, "x", 0, -1])
def test_update_catalog_exercise_invalid_id(exercise_id):
    assert update_exercise(exercise_id).status == FitnessOperationStatus.INVALID_ID


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_catalog_exercise_not_found(mock_repo):
    mock_repo.get_exercise_by_id.return_value = None
    assert update_exercise(99, name="X").status == FitnessOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_update_catalog_exercise_all_fields(mock_repo):
    updated = Exercise(3, "Peso muerto", None, _D, _D, None)
    mock_repo.get_exercise_by_id.side_effect = [_CATALOG_EXERCISE, updated]
    mock_repo.get_active_exercise_by_name.return_value = None

    result = update_exercise(3, name=" Peso muerto ", kind=None)

    assert result.status == FitnessOperationStatus.OK
    assert result.exercise.name == "Peso muerto"
    mock_repo.update_exercise.assert_called_once_with(
        3, name="Peso muerto", kind=None, updated_at=_D
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_catalog_exercise_no_fields_refetches(mock_repo):
    mock_repo.get_exercise_by_id.side_effect = [_CATALOG_EXERCISE, _CATALOG_EXERCISE]

    result = update_exercise(3)

    assert result.status == FitnessOperationStatus.OK
    mock_repo.update_exercise.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_catalog_exercise_duplicate_name_other_id(mock_repo):
    duplicate = Exercise(9, "Peso muerto", None, _D, _D, None)
    mock_repo.get_exercise_by_id.return_value = _CATALOG_EXERCISE
    mock_repo.get_active_exercise_by_name.return_value = duplicate

    result = update_exercise(3, name="Peso muerto")

    assert result.status == FitnessOperationStatus.DUPLICATE_NAME
    mock_repo.update_exercise.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_catalog_exercise_same_name_same_id_allowed(mock_repo):
    mock_repo.get_exercise_by_id.side_effect = [_CATALOG_EXERCISE, _CATALOG_EXERCISE]
    mock_repo.get_active_exercise_by_name.return_value = _CATALOG_EXERCISE

    result = update_exercise(3, name="Sentadilla")

    assert result.status == FitnessOperationStatus.OK
    mock_repo.update_exercise.assert_called_once()


@pytest.mark.unit
@pytest.mark.parametrize("name", [None, "", "   ", 42, "x" * 81])
@patch("modules.fitness.service.repository")
def test_update_catalog_exercise_invalid_name(mock_repo, name):
    mock_repo.get_exercise_by_id.return_value = _CATALOG_EXERCISE

    result = update_exercise(3, name=name)

    assert result.status == FitnessOperationStatus.INVALID_NAME
    mock_repo.update_exercise.assert_not_called()


@pytest.mark.unit
@pytest.mark.parametrize("kind", ["x" * 41])
@patch("modules.fitness.service.repository")
def test_update_catalog_exercise_invalid_kind(mock_repo, kind):
    mock_repo.get_exercise_by_id.return_value = _CATALOG_EXERCISE

    result = update_exercise(3, kind=kind)

    assert result.status == FitnessOperationStatus.INVALID_KIND
    mock_repo.update_exercise.assert_not_called()


# -- catalog: delete_exercise --


@pytest.mark.unit
@pytest.mark.parametrize("exercise_id", [None, "x", 0])
def test_delete_catalog_exercise_invalid_id(exercise_id):
    assert delete_exercise(exercise_id).status == FitnessOperationStatus.INVALID_ID


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_delete_catalog_exercise_not_found(mock_repo):
    mock_repo.get_exercise_by_id.return_value = None
    assert delete_exercise(99).status == FitnessOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_delete_catalog_exercise_ok(mock_repo):
    mock_repo.get_exercise_by_id.return_value = _CATALOG_EXERCISE

    result = delete_exercise(3)

    assert result.status == FitnessOperationStatus.OK
    mock_repo.soft_delete_exercise.assert_called_once_with(3)


# -- workout entries: log_workout --


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_log_workout_full(mock_repo):
    mock_repo.create_workout_entry.return_value = _ENTRY

    result = log_workout(
        1,
        5,
        duration_min=45,
        calories_burned=450.44,
        performed_at="2026-03-14",
        notes="  5km  ",
    )

    assert result.status == FitnessOperationStatus.OK
    mock_repo.create_workout_entry.assert_called_once_with(
        user_id=1,
        exercise_id=5,
        routine_id=None,
        duration_min=45,
        calories_burned=450.4,
        sets_breakdown=[],
        performed_at="2026-03-14",
        notes="5km",
        created_at=_D,
        metrics={},
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_log_workout_defaults(mock_repo):
    entry = WorkoutEntry(2, 1, 6, None, 60, None, [], {}, None, _D, _D)
    mock_repo.create_workout_entry.return_value = entry

    result = log_workout(1, 6, duration_min=60)

    assert result.status == FitnessOperationStatus.OK
    call_kwargs = mock_repo.create_workout_entry.call_args.kwargs
    assert call_kwargs["performed_at"] == _D
    assert call_kwargs["calories_burned"] is None
    assert call_kwargs["sets_breakdown"] == []
    assert call_kwargs["metrics"] == {}


@pytest.mark.unit
@pytest.mark.parametrize("exercise_id", [None, "5", 5.0, True, -1, 0])
def test_log_workout_invalid_exercise_id(exercise_id):
    assert (
        log_workout(1, exercise_id, duration_min=30).status
        == FitnessOperationStatus.INVALID_ID
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_log_workout_unknown_exercise_id(mock_repo):
    mock_repo.get_exercise_by_id.return_value = None

    result = log_workout(1, 999, duration_min=30)

    assert result.status == FitnessOperationStatus.INVALID_EXERCISE_ID
    mock_repo.create_workout_entry.assert_not_called()


@pytest.mark.unit
@pytest.mark.parametrize("duration", ["30", True, 30.5, 0, -10, 1441])
@patch("modules.fitness.service.repository")
def test_log_workout_invalid_duration(mock_repo, duration):
    mock_repo.get_exercise_by_id.return_value = MagicMock()
    assert (
        log_workout(1, 5, duration_min=duration).status
        == FitnessOperationStatus.INVALID_DURATION_MIN
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_log_workout_requires_duration_or_sets(mock_repo):
    mock_repo.get_exercise_by_id.return_value = MagicMock()

    result = log_workout(1, 5)

    assert result.status == FitnessOperationStatus.INVALID_DURATION_MIN
    mock_repo.create_workout_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_log_workout_without_duration_with_sets_ok(mock_repo):
    mock_repo.get_exercise_by_id.return_value = MagicMock()
    mock_repo.create_workout_entry.return_value = _ENTRY

    result = log_workout(
        1, 5, sets_breakdown=[{"exercise_name": "Press", "weight_kg": None, "reps": 12, "sets": 3}]
    )

    assert result.status == FitnessOperationStatus.OK
    kwargs = mock_repo.create_workout_entry.call_args.kwargs
    assert kwargs["duration_min"] is None
    assert kwargs["sets_breakdown"] == [
        {"exercise_id": None, "exercise_name": "Press", "weight_kg": None, "reps": 12, "sets": 3}
    ]


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_log_workout_sets_breakdown_normalizes_without_volume_injection(mock_repo):
    mock_repo.get_exercise_by_id.return_value = MagicMock()
    mock_repo.create_workout_entry.return_value = _ENTRY

    result = log_workout(
        1,
        5,
        duration_min=60,
        sets_breakdown=[
            {
                "exercise_name": " press banca ",
                "weight_kg": 50.0,
                "reps": 8,
                "sets": 3,
                "exercise_id": 7,
            },
            {"exercise_name": "Press", "weight_kg": 61, "reps": 5},
        ],
    )

    assert result.status == FitnessOperationStatus.OK
    kwargs = mock_repo.create_workout_entry.call_args.kwargs
    assert kwargs["sets_breakdown"] == [
        {
            "exercise_id": 7,
            "exercise_name": "Press banca",
            "weight_kg": 50.0,
            "reps": 8,
            "sets": 3,
        },
        {
            "exercise_id": None,
            "exercise_name": "Press",
            "weight_kg": 61.0,
            "reps": 5,
            "sets": 1,
        },
    ]
    assert kwargs["metrics"] == {}


@pytest.mark.unit
@pytest.mark.parametrize(
    "sets_breakdown",
    [
        "nope",
        42,
        {},
        ["row"],
        [{}],
        [{"weight_kg": 0}],
        [{"weight_kg": -1}],
        [{"weight_kg": 501}],
        [{"weight_kg": "50"}],
        [{"weight_kg": True}],
        [{"weight_kg": 50}],
        [{"weight_kg": 50, "reps": 0}],
        [{"weight_kg": 50, "reps": -1}],
        [{"weight_kg": 50, "reps": 1001}],
        [{"weight_kg": 50, "reps": "8"}],
        [{"weight_kg": 50, "reps": True}],
        [{"weight_kg": 50, "reps": 8, "sets": 0}],
        [{"weight_kg": 50, "reps": 8, "sets": 101}],
        [{"weight_kg": 50, "reps": 8, "sets": "3"}],
        [{"weight_kg": 50, "reps": 8, "sets": True}],
        [{"weight_kg": 50, "reps": 8, "exercise_name": "x" * 61}],
        [{"weight_kg": 50, "reps": 8, "exercise_id": 0}],
        [{"weight_kg": 50, "reps": 8, "exercise_id": -1}],
        [{"weight_kg": 50, "reps": 8, "exercise_id": "3"}],
        [{"weight_kg": 50, "reps": 8}],
        [{"weight_kg": 50, "reps": 8, "exercise_name": ""}],
        [{"weight_kg": 50, "reps": 8, "exercise_name": "   "}],
    ],
)
@patch("modules.fitness.service.repository")
def test_log_workout_invalid_sets(mock_repo, sets_breakdown):
    mock_repo.get_exercise_by_id.return_value = MagicMock()
    assert (
        log_workout(1, 5, duration_min=30, sets_breakdown=sets_breakdown).status
        == FitnessOperationStatus.INVALID_SETS_BREAKDOWN
    )


@pytest.mark.unit
@pytest.mark.parametrize("calories", [-1, "300", True])
@patch("modules.fitness.service.repository")
def test_log_workout_invalid_calories(mock_repo, calories):
    mock_repo.get_exercise_by_id.return_value = MagicMock()
    assert (
        log_workout(1, 5, duration_min=30, calories_burned=calories).status
        == FitnessOperationStatus.INVALID_CALORIES_BURNED
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_log_workout_invalid_performed_at(mock_repo):
    mock_repo.get_exercise_by_id.return_value = MagicMock()
    assert (
        log_workout(1, 5, duration_min=30, performed_at="bad").status
        == FitnessOperationStatus.INVALID_PERFORMED_AT
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_list_workout_entries_passthrough(mock_repo):
    mock_repo.get_workout_entries.return_value = [_ENTRY]
    entries = list_workout_entries(1, 5, "2026-03-01", "2026-03-15", 10)
    assert entries == [_ENTRY]
    mock_repo.get_workout_entries.assert_called_once_with(1, 5, "2026-03-01", "2026-03-15", 10)


# -- workout entries: update_workout_entry --


@pytest.mark.unit
@pytest.mark.parametrize("entry_id", [None, "x", 0])
def test_update_workout_entry_invalid_id(entry_id):
    assert update_workout_entry(entry_id, 1).status == FitnessOperationStatus.INVALID_ID


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_workout_entry_not_found(mock_repo):
    mock_repo.get_workout_entry_by_id_and_user.return_value = None
    assert update_workout_entry(99, 1).status == FitnessOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_workout_entry_all_fields(mock_repo):
    updated = WorkoutEntry(1, 1, 7, None, 90, 500.0, [], {"rpe": 8}, "hoy", "2026-03-16", _D)
    mock_repo.get_workout_entry_by_id_and_user.side_effect = [_ENTRY, updated]

    result = update_workout_entry(
        1,
        1,
        exercise_id=7,
        duration_min=90,
        calories_burned=500.0,
        performed_at="2026-03-16",
        notes="hoy",
        metrics={"rpe": 8},
    )

    assert result.status == FitnessOperationStatus.OK
    assert result.workout_entry.exercise_id == 7
    mock_repo.update_workout_entry.assert_called_once_with(
        1,
        1,
        exercise_id=7,
        routine_id=None,
        duration_min=90,
        calories_burned=500.0,
        performed_at="2026-03-16",
        notes="hoy",
        metrics={"rpe": 8},
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_workout_entry_clears_optional_fields(mock_repo):
    mock_repo.get_workout_entry_by_id_and_user.side_effect = [_ENTRY, _ENTRY]

    result = update_workout_entry(1, 1, calories_burned=None, notes=None, metrics={})

    assert result.status == FitnessOperationStatus.OK
    kwargs = mock_repo.update_workout_entry.call_args.kwargs
    assert kwargs["calories_burned"] is None
    assert kwargs["notes"] is None
    assert kwargs["metrics"] == {}


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_workout_entry_sets_breakdown(mock_repo):
    updated = WorkoutEntry(
        1,
        1,
        5,
        None,
        None,
        None,
        [
            {
                "exercise_id": None,
                "exercise_name": "Press",
                "weight_kg": 100.0,
                "reps": 10,
                "sets": 2,
            }
        ],
        {},
        None,
        _D,
        _D,
    )
    mock_repo.get_workout_entry_by_id_and_user.side_effect = [_ENTRY, updated]

    result = update_workout_entry(
        1,
        1,
        duration_min=None,
        sets_breakdown=[
            {"exercise_name": " press ", "weight_kg": 100, "reps": 10, "sets": 2}
        ],
    )

    assert result.status == FitnessOperationStatus.OK
    kwargs = mock_repo.update_workout_entry.call_args.kwargs
    assert kwargs["duration_min"] is None
    assert kwargs["sets_breakdown"] == [
        {"exercise_id": None, "exercise_name": "Press", "weight_kg": 100.0, "reps": 10, "sets": 2}
    ]


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_workout_entry_clears_sets(mock_repo):
    entry_with_sets = WorkoutEntry(
        1,
        1,
        5,
        None,
        45,
        None,
        [{"exercise_id": None, "exercise_name": "Press", "weight_kg": 50.0, "reps": 8, "sets": 3}],
        {},
        None,
        _D,
        _D,
    )
    mock_repo.get_workout_entry_by_id_and_user.side_effect = [entry_with_sets, _ENTRY]

    for value in ([], None):
        mock_repo.update_workout_entry.reset_mock()
        mock_repo.get_workout_entry_by_id_and_user.side_effect = [entry_with_sets, _ENTRY]
        result = update_workout_entry(1, 1, sets_breakdown=value)
        assert result.status == FitnessOperationStatus.OK, value
        assert mock_repo.update_workout_entry.call_args.kwargs["sets_breakdown"] == []


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_workout_entry_cannot_remove_both_duration_and_sets(mock_repo):
    mock_repo.get_workout_entry_by_id_and_user.return_value = _ENTRY

    result = update_workout_entry(1, 1, duration_min=None)

    assert result.status == FitnessOperationStatus.INVALID_DURATION_MIN
    mock_repo.update_workout_entry.assert_not_called()

    sets_only = WorkoutEntry(
        1,
        1,
        5,
        None,
        None,
        None,
        [{"exercise_id": None, "exercise_name": "Press", "weight_kg": 50.0, "reps": 8, "sets": 3}],
        {},
        None,
        _D,
        _D,
    )
    mock_repo.get_workout_entry_by_id_and_user.return_value = sets_only

    result = update_workout_entry(1, 1, sets_breakdown=[])

    assert result.status == FitnessOperationStatus.INVALID_DURATION_MIN
    mock_repo.update_workout_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_log_workout_routine_breakdown_requires_exercise_ids(mock_repo):
    mock_repo.get_routine_by_id.return_value = MagicMock()
    mock_repo.get_routine_exercises.return_value = [MagicMock()]
    mock_repo.create_workout_entry.return_value = _ENTRY

    result = log_workout(
        1,
        routine_id=5,
        duration_min=30,
        sets_breakdown=[
            {
                "exercise_name": "Press",
                "weight_kg": 50.0,
                "reps": 8,
                "sets": 3,
                "exercise_id": 7,
            },
            {"exercise_name": "Sentadilla", "weight_kg": 80.0, "reps": 10, "sets": 4},
        ],
    )

    assert result.status == FitnessOperationStatus.INVALID_SETS_BREAKDOWN
    mock_repo.create_workout_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_workout_entry_switch_to_routine_normalizes(mock_repo):
    mock_repo.get_routine_by_id.return_value = MagicMock()
    mock_repo.get_workout_entry_by_id_and_user.side_effect = [_ENTRY, _ENTRY]

    result = update_workout_entry(
        1,
        1,
        routine_id=5,
        duration_min=60,
        sets_breakdown=[
            {"exercise_name": "Press", "weight_kg": 50.0, "reps": 8, "sets": 3, "exercise_id": 7}
        ],
    )

    assert result.status == FitnessOperationStatus.OK
    kwargs = mock_repo.update_workout_entry.call_args.kwargs
    assert kwargs["routine_id"] == 5
    assert kwargs["exercise_id"] is None


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_workout_entry_switch_to_exercise_normalizes(mock_repo):
    mock_repo.get_exercise_by_id.return_value = MagicMock()
    routine_entry = WorkoutEntry(1, 1, None, 5, 45, None, [], {}, None, _D, _D)
    mock_repo.get_workout_entry_by_id_and_user.side_effect = [routine_entry, routine_entry]

    result = update_workout_entry(1, 1, exercise_id=5, duration_min=60)

    assert result.status == FitnessOperationStatus.OK
    kwargs = mock_repo.update_workout_entry.call_args.kwargs
    assert kwargs["exercise_id"] == 5
    assert kwargs["routine_id"] is None


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_workout_entry_routine_breakdown_requires_exercise_ids(mock_repo):
    mock_repo.get_routine_by_id.return_value = MagicMock()
    mock_repo.get_workout_entry_by_id_and_user.side_effect = [_ENTRY, _ENTRY]

    result = update_workout_entry(
        1,
        1,
        routine_id=5,
        duration_min=60,
        sets_breakdown=[
            {"exercise_name": "Press", "weight_kg": 50.0, "reps": 8, "sets": 3}
        ],
    )

    assert result.status == FitnessOperationStatus.INVALID_SETS_BREAKDOWN
    mock_repo.update_workout_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_workout_entry_field_validation(mock_repo):
    cases = [
        {"exercise_id": 0},
        {"exercise_id": "x"},
        {"duration_min": "x"},
        {"duration_min": 1441},
        {"calories_burned": -5},
        {"calories_burned": "x"},
        {"performed_at": "nope"},
        {"metrics": "nope"},
        {"sets_breakdown": "nope"},
        {"sets_breakdown": [{"weight_kg": -1}]},
    ]
    for fields in cases:
        mock_repo.get_workout_entry_by_id_and_user.return_value = _ENTRY
        mock_repo.get_exercise_by_id.return_value = MagicMock()
        result = update_workout_entry(1, 1, **fields)
        assert result.status != FitnessOperationStatus.OK, fields


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_workout_entry_row_missing_after_update(mock_repo):
    mock_repo.get_workout_entry_by_id_and_user.side_effect = [_ENTRY, None]

    result = update_workout_entry(1, 1, notes="x")

    assert result.status == FitnessOperationStatus.NOT_FOUND


# -- workout entries: delete_workout_entry --


@pytest.mark.unit
@pytest.mark.parametrize("entry_id", [None, "x", 0])
def test_delete_workout_entry_invalid_id(entry_id):
    assert delete_workout_entry(entry_id, 1).status == FitnessOperationStatus.INVALID_ID


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_delete_workout_entry_not_found(mock_repo):
    mock_repo.get_workout_entry_by_id_and_user.return_value = None
    assert delete_workout_entry(99, 1).status == FitnessOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_delete_workout_entry_ok(mock_repo):
    mock_repo.get_workout_entry_by_id_and_user.return_value = _ENTRY

    result = delete_workout_entry(1, 1)

    assert result.status == FitnessOperationStatus.OK
    mock_repo.delete_workout_entry.assert_called_once_with(1, 1)


# -- stats --


@pytest.mark.unit
@patch("modules.fitness.service.get_today", _mock_today)
@patch("modules.fitness.service.repository")
def test_get_stats_full(mock_repo):
    latest = WeightEntry(1, 1, 78.0, None, "2026-03-15", _D)
    baseline_7d = WeightEntry(2, 1, 80.0, None, "2026-03-07", _D)
    baseline_30d = WeightEntry(3, 1, 82.0, None, "2026-02-20", _D)
    correr = Exercise(10, "correr", None, _D, _D, None)
    gym = Exercise(11, "gym", None, _D, _D, _D)
    yoga = Exercise(12, "yoga", None, _D, _D, None)
    ex_7d = [
        WorkoutEntry(1, 1, 10, None, 30, None, [], {}, None, "2026-03-14", _D),
        WorkoutEntry(2, 1, 11, None, 60, None, [], {}, None, "2026-03-12", _D),
    ]
    ex_30d = ex_7d + [WorkoutEntry(3, 1, 12, None, 90, None, [], {}, None, "2026-03-01", _D)]

    mock_repo.get_weight_entries.return_value = [latest]
    mock_repo.get_earliest_weight_on_or_after.side_effect = [baseline_7d, baseline_30d]
    mock_repo.get_workout_entries.side_effect = [ex_7d, ex_30d]
    mock_repo.get_exercises.return_value = [correr, gym, yoga]

    stats = get_fitness_stats(1)

    assert stats.latest_weight_kg == 78.0
    assert stats.latest_measured_at == "2026-03-15"
    assert stats.weight_delta_7d == -2.0
    assert stats.weight_delta_30d == -4.0
    assert stats.minutes_last_7d == 90
    assert stats.sessions_last_7d == 2
    assert stats.minutes_last_30d == 180
    assert stats.sessions_last_30d == 3
    assert stats.volume_kg_last_7d is None
    assert stats.volume_kg_last_30d is None
    assert stats.reps_last_7d == 0
    assert stats.reps_last_30d == 0
    assert stats.by_exercise_last_30d == {
        "yoga": {"minutes": 90, "count": 1},
        "gym": {"minutes": 60, "count": 1},
        "correr": {"minutes": 30, "count": 1},
    }


@pytest.mark.unit
@patch("modules.fitness.service.get_today", _mock_today)
@patch("modules.fitness.service.repository")
def test_get_stats_routine_breakdown_counts_exercises(mock_repo):
    correr = Exercise(10, "correr", None, _D, _D, None)
    press = Exercise(20, "press", None, _D, _D, None)
    sentadilla = Exercise(21, "sentadilla", None, _D, _D, None)
    ex_30d = [
        WorkoutEntry(
            1,
            1,
            10,
            None,
            30,
            None,
            [],
            {},
            None,
            "2026-03-10",
            _D,
        ),
        WorkoutEntry(
            2,
            1,
            None,
            5,
            60,
            None,
            [
                {
                    "exercise_id": 20,
                    "exercise_name": "press",
                    "weight_kg": 50.0,
                    "reps": 8,
                    "sets": 3,
                },
                {
                    "exercise_id": 21,
                    "exercise_name": "sentadilla",
                    "weight_kg": 80.0,
                    "reps": 10,
                    "sets": 4,
                },
            ],
            {},
            None,
            "2026-03-12",
            _D,
        ),
    ]

    mock_repo.get_weight_entries.return_value = []
    mock_repo.get_earliest_weight_on_or_after.return_value = MagicMock()
    mock_repo.get_workout_entries.side_effect = [ex_30d, ex_30d]
    mock_repo.get_exercises.return_value = [correr, press, sentadilla]

    stats = get_fitness_stats(1)

    assert stats.by_exercise_last_30d == {
        "press": {"minutes": 0, "count": 1},
        "sentadilla": {"minutes": 0, "count": 1},
        "correr": {"minutes": 30, "count": 1},
    }


@pytest.mark.unit
@patch("modules.fitness.service.get_today", _mock_today)
@patch("modules.fitness.service.repository")
def test_get_stats_volume_totals(mock_repo):
    loaded = WorkoutEntry(
        1,
        1,
        10,
        None,
        45,
        None,
        [
            {
                "exercise_id": None,
                "exercise_name": "Press",
                "weight_kg": 60.0,
                "reps": 8,
                "sets": 3,
            },
            {
                "exercise_id": None,
                "exercise_name": "Press",
                "weight_kg": None,
                "reps": 10,
                "sets": 2,
            },
        ],
        {},
        None,
        "2026-03-14",
        _D,
    )
    bodyweight_only = WorkoutEntry(
        2,
        1,
        11,
        None,
        None,
        None,
        [
            {
                "exercise_id": None,
                "exercise_name": "Press",
                "weight_kg": None,
                "reps": 15,
                "sets": 3,
            }
        ],
        {},
        None,
        "2026-03-12",
        _D,
    )

    mock_repo.get_weight_entries.return_value = []
    mock_repo.get_earliest_weight_on_or_after.return_value = MagicMock()
    mock_repo.get_workout_entries.side_effect = [[loaded], [loaded, bodyweight_only]]
    mock_repo.get_exercises.return_value = []

    stats = get_fitness_stats(1)

    assert stats.volume_kg_last_7d == 1440.0
    assert stats.reps_last_7d == 44
    assert stats.volume_kg_last_30d == 1440.0
    assert stats.reps_last_30d == 89


@pytest.mark.unit
@patch("modules.fitness.service.get_today", _mock_today)
@patch("modules.fitness.service.repository")
def test_get_stats_unknown_exercise_falls_back_to_id(mock_repo):
    ex_30d = [WorkoutEntry(1, 1, 42, None, 25, None, [], {}, None, "2026-03-10", _D)]
    mock_repo.get_weight_entries.return_value = []
    mock_repo.get_earliest_weight_on_or_after.return_value = MagicMock()
    mock_repo.get_workout_entries.return_value = ex_30d
    mock_repo.get_exercises.return_value = []

    stats = get_fitness_stats(1)

    assert stats.by_exercise_last_30d == {"#42": {"minutes": 25, "count": 1}}


@pytest.mark.unit
@patch("modules.fitness.service.get_today", _mock_today)
@patch("modules.fitness.service.repository")
def test_get_stats_empty(mock_repo):
    mock_repo.get_weight_entries.return_value = []
    mock_repo.get_earliest_weight_on_or_after.return_value = MagicMock()
    mock_repo.get_workout_entries.return_value = []
    mock_repo.get_exercises.return_value = []

    stats = get_fitness_stats(1)

    assert stats.latest_weight_kg is None
    assert stats.weight_delta_7d is None
    assert stats.weight_delta_30d is None
    assert stats.minutes_last_7d == 0
    assert stats.sessions_last_7d == 0


# -- workout entry metrics --


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_log_workout_with_scalar_and_string_metrics(mock_repo):
    mock_repo.create_workout_entry.return_value = _ENTRY

    result = log_workout(
        1, 5, duration_min=30, metrics={"distance_km": 5.4321, "surface": "  asfalto  "}
    )

    assert result.status == FitnessOperationStatus.OK
    kwargs = mock_repo.create_workout_entry.call_args.kwargs
    assert kwargs["metrics"] == {"distance_km": 5.43, "surface": "asfalto"}


@pytest.mark.unit
@pytest.mark.parametrize(
    "metrics",
    [
        "nope",
        42,
        ["row"],
        True,
        {f"k{i}": i for i in range(16)},
        {"": 1},
        {"   ": 1},
        {"k" * 41: 1},
        {"m": True},
        {"m": None},
        {"m": [1]},
        {"m": {"n": 1}},
        {"m": ""},
        {"m": "   "},
        {"m": "v" * 51},
    ],
)
@patch("modules.fitness.service.repository")
def test_log_workout_invalid_metrics(mock_repo, metrics):
    mock_repo.get_exercise_by_id.return_value = MagicMock()
    assert (
        log_workout(1, 5, duration_min=30, metrics=metrics).status
        == FitnessOperationStatus.INVALID_METRICS
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_workout_entry_with_metrics(mock_repo):
    updated = WorkoutEntry(1, 1, 5, None, 90, None, [], {"rpe": 8}, None, _D, _D)
    mock_repo.get_workout_entry_by_id_and_user.side_effect = [_ENTRY, updated]

    result = update_workout_entry(1, 1, metrics={"rpe": 8})

    assert result.status == FitnessOperationStatus.OK
    mock_repo.update_workout_entry.assert_called_once_with(1, 1, metrics={"rpe": 8})


@pytest.mark.unit
@pytest.mark.parametrize(
    "metrics",
    [
        True,
        {"m": [1]},
        {"m": {"n": 1}},
    ],
)
@patch("modules.fitness.service.repository")
def test_update_workout_entry_invalid_metrics(mock_repo, metrics):
    mock_repo.get_workout_entry_by_id_and_user.return_value = _ENTRY

    result = update_workout_entry(1, 1, metrics=metrics)

    assert result.status == FitnessOperationStatus.INVALID_METRICS
    mock_repo.update_workout_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_workout_entry_clears_metrics(mock_repo):
    mock_repo.get_workout_entry_by_id_and_user.side_effect = [_ENTRY, _ENTRY]

    result = update_workout_entry(1, 1, metrics={})

    assert result.status == FitnessOperationStatus.OK
    kwargs = mock_repo.update_workout_entry.call_args.kwargs
    assert kwargs["metrics"] == {}


# -- routines: create_routine --


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_create_routine_full(mock_repo):
    mock_repo.get_active_routine_by_name.return_value = None
    mock_repo.get_exercise_by_id.return_value = _CATALOG_EXERCISE
    mock_repo.create_routine.return_value = _ROUTINE
    mock_repo.set_routine_exercises.return_value = [_ROUTINE_EXERCISE]

    result = create_routine(
        "  Push day  ",
        category=" fuerza ",
        description="  pecho  ",
        exercises=[{"exercise_id": 3, "weight_kg": 50, "reps": 8, "sets": 3}],
    )

    assert result.status == FitnessOperationStatus.OK
    assert result.routine.name == "Push day"
    assert result.routine_exercises == [_ROUTINE_EXERCISE]
    mock_repo.create_routine.assert_called_once_with(
        name="Push day", category="fuerza", description="pecho", created_at=_D, updated_at=_D
    )
    mock_repo.set_routine_exercises.assert_called_once_with(
        1, [{"exercise_id": 3, "weight_kg": 50.0, "reps": 8, "sets": 3, "position": 0}]
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_create_routine_defaults(mock_repo):
    mock_repo.get_active_routine_by_name.return_value = None
    mock_repo.create_routine.return_value = _ROUTINE

    result = create_routine("Push day")

    assert result.status == FitnessOperationStatus.OK
    assert result.routine_exercises == []
    kwargs = mock_repo.create_routine.call_args.kwargs
    assert kwargs["category"] is None
    assert kwargs["description"] is None
    mock_repo.set_routine_exercises.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_create_routine_blank_category_description_normalize_to_none(mock_repo):
    mock_repo.get_active_routine_by_name.return_value = None
    mock_repo.create_routine.return_value = _ROUTINE

    result = create_routine("Push day", category="   ", description="  ")

    assert result.status == FitnessOperationStatus.OK
    kwargs = mock_repo.create_routine.call_args.kwargs
    assert kwargs["category"] is None
    assert kwargs["description"] is None


@pytest.mark.unit
@pytest.mark.parametrize("name", [None, "", "   ", 42, "x" * 81])
def test_create_routine_invalid_name(name):
    assert create_routine(name).status == FitnessOperationStatus.INVALID_NAME


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_create_routine_duplicate_name(mock_repo):
    mock_repo.get_active_routine_by_name.return_value = _ROUTINE

    result = create_routine("Push day")

    assert result.status == FitnessOperationStatus.DUPLICATE_NAME
    mock_repo.create_routine.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_create_routine_invalid_category(mock_repo):
    mock_repo.get_active_routine_by_name.return_value = None
    assert create_routine("Push day", category="x" * 41).status == (
        FitnessOperationStatus.INVALID_ROUTINE_CATEGORY
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_create_routine_invalid_description(mock_repo):
    mock_repo.get_active_routine_by_name.return_value = None
    assert create_routine("Push day", description="x" * 501).status == (
        FitnessOperationStatus.INVALID_ROUTINE_DESCRIPTION
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_create_routine_sorts_and_rounds_exercises(mock_repo):
    mock_repo.get_active_routine_by_name.return_value = None
    mock_repo.get_exercise_by_id.return_value = _CATALOG_EXERCISE
    mock_repo.create_routine.return_value = _ROUTINE
    mock_repo.set_routine_exercises.return_value = []

    create_routine(
        "Push",
        exercises=[
            {"exercise_id": 3, "weight_kg": 50.123, "reps": 8, "position": 2},
            {"exercise_id": 4, "reps": 10},
        ],
    )

    call = mock_repo.set_routine_exercises.call_args.args[1]
    assert [(e["exercise_id"], e["position"]) for e in call] == [(4, 0), (3, 1)]
    assert call[0]["weight_kg"] is None
    assert call[1]["weight_kg"] == 50.12


@pytest.mark.unit
@pytest.mark.parametrize(
    "exercises",
    [
        "nope",
        42,
        {},
        ["row"],
        [{}],
        [{"exercise_id": "3", "reps": 8}],
        [{"exercise_id": True, "reps": 8}],
        [{"exercise_id": 0, "reps": 8}],
        [{"exercise_id": -1, "reps": 8}],
        [{"exercise_id": 3, "reps": 8}, {"exercise_id": 3, "reps": 8}],
        [{"exercise_id": 3, "weight_kg": 0, "reps": 8}],
        [{"exercise_id": 3, "weight_kg": -1, "reps": 8}],
        [{"exercise_id": 3, "weight_kg": 501, "reps": 8}],
        [{"exercise_id": 3, "weight_kg": "50", "reps": 8}],
        [{"exercise_id": 3, "reps": 0}],
        [{"exercise_id": 3, "reps": -1}],
        [{"exercise_id": 3, "reps": 1001}],
        [{"exercise_id": 3, "reps": "8"}],
        [{"exercise_id": 3, "reps": True}],
        [{"exercise_id": 3, "reps": 8, "sets": 0}],
        [{"exercise_id": 3, "reps": 8, "sets": 101}],
        [{"exercise_id": 3, "reps": 8, "sets": "3"}],
        [{"exercise_id": 3, "reps": 8, "sets": True}],
        [{"exercise_id": 3, "reps": 8, "position": "x"}],
        [{"exercise_id": 3, "reps": 8, "position": -1}],
        [{"exercise_id": 3, "reps": 8, "position": True}],
    ],
)
@patch("modules.fitness.service.repository")
def test_create_routine_invalid_exercises(mock_repo, exercises):
    mock_repo.get_active_routine_by_name.return_value = None
    mock_repo.get_exercise_by_id.return_value = _CATALOG_EXERCISE

    result = create_routine("Push day", exercises=exercises)

    assert result.status == FitnessOperationStatus.INVALID_ROUTINE_EXERCISES
    mock_repo.create_routine.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_create_routine_unknown_exercise_id(mock_repo):
    mock_repo.get_active_routine_by_name.return_value = None
    mock_repo.get_exercise_by_id.return_value = None

    result = create_routine("Push day", exercises=[{"exercise_id": 999, "reps": 8}])

    assert result.status == FitnessOperationStatus.INVALID_ROUTINE_EXERCISES


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_create_routine_too_many_exercises(mock_repo):
    mock_repo.get_active_routine_by_name.return_value = None
    mock_repo.get_exercise_by_id.return_value = _CATALOG_EXERCISE

    result = create_routine("Push day", exercises=[{"exercise_id": 3, "reps": 8}] * 51)

    assert result.status == FitnessOperationStatus.INVALID_ROUTINE_EXERCISES


# -- routines: list / details --


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_list_routines_passthrough(mock_repo):
    mock_repo.get_routines.return_value = [_ROUTINE]
    assert list_routines() == [_ROUTINE]
    mock_repo.get_routines.assert_called_once_with(include_deleted=False)


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_get_routine_name_map(mock_repo):
    other = Routine(9, "Leg day", None, None, _D, _D, None)
    mock_repo.get_routines.return_value = [_ROUTINE, other]

    names = get_routine_name_map()

    assert names == {1: "Push day", 9: "Leg day"}
    mock_repo.get_routines.assert_called_once_with(include_deleted=True)


@pytest.mark.unit
@pytest.mark.parametrize("routine_id", [None, "x", 0])
def test_get_routine_details_invalid_id(routine_id):
    assert get_routine_details(routine_id).status == FitnessOperationStatus.INVALID_ROUTINE_ID


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_get_routine_details_not_found(mock_repo):
    mock_repo.get_routine_by_id.return_value = None
    assert get_routine_details(99).status == FitnessOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_get_routine_details_ok(mock_repo):
    mock_repo.get_routine_by_id.return_value = _ROUTINE
    mock_repo.get_routine_exercises.return_value = [_ROUTINE_EXERCISE]

    result = get_routine_details(1)

    assert result.status == FitnessOperationStatus.OK
    assert result.routine is _ROUTINE
    assert result.routine_exercises == [_ROUTINE_EXERCISE]


# -- routines: update_routine --


@pytest.mark.unit
@pytest.mark.parametrize("routine_id", [None, "x", 0])
def test_update_routine_invalid_id(routine_id):
    assert update_routine(routine_id).status == FitnessOperationStatus.INVALID_ROUTINE_ID


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_routine_not_found(mock_repo):
    mock_repo.get_routine_by_id.return_value = None
    assert update_routine(99, name="X").status == FitnessOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_update_routine_all_fields(mock_repo):
    updated = Routine(1, "Pull day", "espalda", "jalones", _D, _D, None)
    mock_repo.get_routine_by_id.side_effect = [_ROUTINE, updated]
    mock_repo.get_active_routine_by_name.return_value = None

    result = update_routine(1, name=" Pull day ", category=" espalda ", description="jalones")

    assert result.status == FitnessOperationStatus.OK
    assert result.routine.name == "Pull day"
    mock_repo.update_routine.assert_called_once_with(
        1, name="Pull day", category="espalda", description="jalones", updated_at=_D
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_routine_no_fields_refetches(mock_repo):
    mock_repo.get_routine_by_id.side_effect = [_ROUTINE, _ROUTINE]

    result = update_routine(1)

    assert result.status == FitnessOperationStatus.OK
    mock_repo.update_routine.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_routine_duplicate_name_other_id(mock_repo):
    duplicate = Routine(9, "Pull day", None, None, _D, _D, None)
    mock_repo.get_routine_by_id.return_value = _ROUTINE
    mock_repo.get_active_routine_by_name.return_value = duplicate

    result = update_routine(1, name="Pull day")

    assert result.status == FitnessOperationStatus.DUPLICATE_NAME
    mock_repo.update_routine.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_routine_same_name_same_id_allowed(mock_repo):
    mock_repo.get_routine_by_id.side_effect = [_ROUTINE, _ROUTINE]
    mock_repo.get_active_routine_by_name.return_value = _ROUTINE

    result = update_routine(1, name="Push day")

    assert result.status == FitnessOperationStatus.OK
    mock_repo.update_routine.assert_called_once()


@pytest.mark.unit
@pytest.mark.parametrize("name", [None, "", "   ", 42, "x" * 81])
@patch("modules.fitness.service.repository")
def test_update_routine_invalid_name(mock_repo, name):
    mock_repo.get_routine_by_id.return_value = _ROUTINE

    result = update_routine(1, name=name)

    assert result.status == FitnessOperationStatus.INVALID_NAME
    mock_repo.update_routine.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_routine_invalid_category(mock_repo):
    mock_repo.get_routine_by_id.return_value = _ROUTINE

    result = update_routine(1, category="x" * 41)

    assert result.status == FitnessOperationStatus.INVALID_ROUTINE_CATEGORY
    mock_repo.update_routine.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_routine_invalid_description(mock_repo):
    mock_repo.get_routine_by_id.return_value = _ROUTINE

    result = update_routine(1, description="x" * 501)

    assert result.status == FitnessOperationStatus.INVALID_ROUTINE_DESCRIPTION
    mock_repo.update_routine.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_routine_row_missing_after_update(mock_repo):
    mock_repo.get_routine_by_id.side_effect = [_ROUTINE, None]
    mock_repo.get_active_routine_by_name.return_value = None

    result = update_routine(1, name="Pull day")

    assert result.status == FitnessOperationStatus.NOT_FOUND


# -- routines: replace_routine_exercises --


@pytest.mark.unit
@pytest.mark.parametrize("routine_id", [None, "x", 0])
def test_replace_routine_exercises_invalid_id(routine_id):
    assert replace_routine_exercises(routine_id, []).status == (
        FitnessOperationStatus.INVALID_ROUTINE_ID
    )


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_replace_routine_exercises_not_found(mock_repo):
    mock_repo.get_routine_by_id.return_value = None
    assert replace_routine_exercises(99, []).status == FitnessOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_replace_routine_exercises_invalid_exercises(mock_repo):
    mock_repo.get_routine_by_id.return_value = _ROUTINE

    result = replace_routine_exercises(1, [{"exercise_id": 0, "reps": 8}])

    assert result.status == FitnessOperationStatus.INVALID_ROUTINE_EXERCISES


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_replace_routine_exercises_ok(mock_repo):
    mock_repo.get_routine_by_id.side_effect = [_ROUTINE, _ROUTINE]
    mock_repo.get_exercise_by_id.return_value = _CATALOG_EXERCISE
    mock_repo.set_routine_exercises.return_value = [_ROUTINE_EXERCISE]

    result = replace_routine_exercises(1, [{"exercise_id": 3, "reps": 8}])

    assert result.status == FitnessOperationStatus.OK
    assert result.routine_exercises == [_ROUTINE_EXERCISE]
    mock_repo.set_routine_exercises.assert_called_once_with(
        1, [{"exercise_id": 3, "weight_kg": None, "reps": 8, "sets": 1, "position": 0}]
    )


# -- routines: delete_routine --


@pytest.mark.unit
@pytest.mark.parametrize("routine_id", [None, "x", 0])
def test_delete_routine_invalid_id(routine_id):
    assert delete_routine(routine_id).status == FitnessOperationStatus.INVALID_ROUTINE_ID


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_delete_routine_not_found(mock_repo):
    mock_repo.get_routine_by_id.return_value = None
    assert delete_routine(99).status == FitnessOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_delete_routine_ok(mock_repo):
    mock_repo.get_routine_by_id.return_value = _ROUTINE

    result = delete_routine(1)

    assert result.status == FitnessOperationStatus.OK
    mock_repo.soft_delete_routine.assert_called_once_with(1)


# -- routines: log_workout / update_workout_entry routine branches --


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_log_workout_unknown_routine_id(mock_repo):
    mock_repo.get_routine_by_id.return_value = None

    result = log_workout(1, routine_id=999, duration_min=30)

    assert result.status == FitnessOperationStatus.INVALID_ROUTINE_ID
    mock_repo.create_workout_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
@patch("modules.fitness.service.get_today", _mock_today)
def test_log_workout_with_routine(mock_repo):
    mock_repo.get_routine_by_id.return_value = MagicMock()
    mock_repo.get_routine_exercises.return_value = [MagicMock()]
    mock_repo.create_workout_entry.return_value = _ENTRY

    result = log_workout(
        1,
        routine_id=5,
        duration_min=45,
        sets_breakdown=[
            {"exercise_id": 7, "exercise_name": "Press", "weight_kg": 50.0, "reps": 8, "sets": 3}
        ],
    )

    assert result.status == FitnessOperationStatus.OK
    kwargs = mock_repo.create_workout_entry.call_args.kwargs
    assert kwargs["routine_id"] == 5
    assert kwargs["exercise_id"] is None
    assert kwargs["duration_min"] == 45


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_log_workout_routine_without_exercises(mock_repo):
    mock_repo.get_routine_by_id.return_value = MagicMock()
    mock_repo.get_routine_exercises.return_value = []

    result = log_workout(1, routine_id=5, duration_min=30)

    assert result.status == FitnessOperationStatus.INVALID_ROUTINE_EXERCISES
    mock_repo.create_workout_entry.assert_not_called()


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_workout_entry_invalid_routine_id(mock_repo):
    mock_repo.get_workout_entry_by_id_and_user.return_value = _ENTRY
    mock_repo.get_routine_by_id.return_value = None

    result = update_workout_entry(1, 1, routine_id=999)

    assert result.status == FitnessOperationStatus.INVALID_ROUTINE_ID


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_workout_entry_both_routine_and_exercise(mock_repo):
    mock_repo.get_workout_entry_by_id_and_user.return_value = _ENTRY
    mock_repo.get_routine_by_id.return_value = MagicMock()
    mock_repo.get_exercise_by_id.return_value = MagicMock()

    result = update_workout_entry(1, 1, exercise_id=5, routine_id=5, duration_min=60)

    assert result.status == FitnessOperationStatus.INVALID_ID


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_workout_entry_repo_update_fails(mock_repo):
    mock_repo.get_workout_entry_by_id_and_user.return_value = _ENTRY
    mock_repo.update_workout_entry.return_value = False

    result = update_workout_entry(1, 1, notes="x")

    assert result.status == FitnessOperationStatus.NOT_FOUND


# -- gaps: exercise / weight entry / stats --


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_catalog_exercise_refetch_missing(mock_repo):
    mock_repo.get_active_exercise_by_name.return_value = None
    mock_repo.get_exercise_by_id.side_effect = [_CATALOG_EXERCISE, None]

    result = update_exercise(3, name="Peso muerto")

    assert result.status == FitnessOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_weight_entry_repo_conflict(mock_repo):
    mock_repo.get_weight_entry_by_id_and_user.return_value = _WEIGHT
    mock_repo.get_weight_entry_by_user_and_date.return_value = None
    mock_repo.update_weight_entry.side_effect = WeightEntryDateConflictError(_WEIGHT)

    result = update_weight_entry(1, 1, measured_at="2026-03-14")

    assert result.status == FitnessOperationStatus.DUPLICATE_DATE


@pytest.mark.unit
@patch("modules.fitness.service.repository")
def test_update_weight_entry_refetch_missing(mock_repo):
    mock_repo.get_weight_entry_by_id_and_user.side_effect = [_WEIGHT, None]

    result = update_weight_entry(1, 1, notes="x")

    assert result.status == FitnessOperationStatus.NOT_FOUND


@pytest.mark.unit
@pytest.mark.parametrize(
    "sets_breakdown",
    [
        [{"exercise_name": "press", "weight_kg": 501}],
        [{"exercise_name": "press", "weight_kg": -1}],
        [{"exercise_name": "press", "weight_kg": "50"}],
        [{"exercise_name": "press", "weight_kg": True}],
        [{"exercise_name": "press", "reps": 0}],
        [{"exercise_name": "press", "reps": -1}],
        [{"exercise_name": "press", "reps": 1001}],
        [{"exercise_name": "press", "reps": "8"}],
        [{"exercise_name": "press", "reps": True}],
        [{"exercise_name": "press", "reps": 8, "sets": 0}],
        [{"exercise_name": "press", "reps": 8, "sets": 101}],
        [{"exercise_name": "press", "reps": 8, "sets": "3"}],
        [{"exercise_name": "press", "reps": 8, "sets": True}],
    ],
)
@patch("modules.fitness.service.repository")
def test_log_workout_invalid_sets_with_name(mock_repo, sets_breakdown):
    mock_repo.get_exercise_by_id.return_value = MagicMock()

    assert (
        log_workout(1, 5, duration_min=30, sets_breakdown=sets_breakdown).status
        == FitnessOperationStatus.INVALID_SETS_BREAKDOWN
    )


@pytest.mark.unit
@patch("modules.fitness.service.get_today", _mock_today)
@patch("modules.fitness.service.repository")
def test_get_stats_routine_breakdown_skips_rows_without_exercise_id(mock_repo):
    ex_30d = [
        WorkoutEntry(
            1,
            1,
            None,
            5,
            60,
            None,
            [
                {
                    "exercise_id": None,
                    "exercise_name": "press",
                    "weight_kg": 50.0,
                    "reps": 8,
                    "sets": 3,
                }
            ],
            {},
            None,
            "2026-03-12",
            _D,
        )
    ]

    mock_repo.get_weight_entries.return_value = []
    mock_repo.get_earliest_weight_on_or_after.return_value = MagicMock()
    mock_repo.get_workout_entries.side_effect = [ex_30d, ex_30d]
    mock_repo.get_exercises.return_value = []

    stats = get_fitness_stats(1)

    assert stats.by_exercise_last_30d == {}
