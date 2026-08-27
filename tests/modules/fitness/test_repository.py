import pytest

import modules.fitness.repository as repository
from modules.fitness.errors import (
    ExerciseAlreadyExistsError,
    RoutineAlreadyExistsError,
    WeightEntryDateConflictError,
)

_D = "2026-03-15"
_USER_ID = 1


# -- Catalog --


@pytest.mark.integration
def test_create_and_get_catalog_exercise(db, db_user):
    created = repository.create_exercise("Sentadilla", "piernas", _D, _D)

    assert created.id > 0
    assert created.name == "Sentadilla"
    assert created.kind == "piernas"
    assert created.created_at == _D
    assert created.updated_at == _D
    assert created.deleted_at is None

    found = repository.get_exercise_by_id(created.id)
    assert found is not None
    assert found.name == "Sentadilla"

    by_name = repository.get_active_exercise_by_name("sentadilla")
    assert by_name is not None
    assert by_name.id == created.id

    by_name = repository.get_active_exercise_by_name("SENTADILLA")
    assert by_name is not None
    assert by_name.id == created.id

    assert repository.get_active_exercise_by_name("Peso muerto") is None


@pytest.mark.integration
def test_create_catalog_exercise_unique_name(db, db_user):
    repository.create_exercise("Press banca", None, _D, _D)

    with pytest.raises(Exception):
        repository.create_exercise("Press banca", "pecho", _D, _D)

    with pytest.raises(Exception):
        repository.create_exercise("press BANCA", "pecho", _D, _D)


@pytest.mark.integration
def test_get_exercises_orders_by_name(db, db_user):
    repository.create_exercise("zumba", None, _D, _D)
    repository.create_exercise("Abdominales", None, _D, _D)
    repository.create_exercise("correr", None, _D, _D)

    names = [e.name for e in repository.get_exercises()]

    assert names == ["Abdominales", "Correr", "Zumba"]


@pytest.mark.integration
def test_soft_delete_hides_from_default_queries(db, db_user):
    created = repository.create_exercise("Yoga", None, _D, _D)

    assert repository.soft_delete_exercise(created.id) is True
    assert repository.soft_delete_exercise(created.id) is False
    assert repository.get_exercise_by_id(created.id) is None
    assert repository.get_active_exercise_by_name("yoga") is None
    assert len(repository.get_exercises()) == 0

    deleted = repository.get_exercises(include_deleted=True)
    assert len(deleted) == 1
    assert deleted[0].deleted_at is not None


@pytest.mark.integration
def test_name_reusable_after_soft_delete(db, db_user):
    first = repository.create_exercise("Yoga", None, _D, _D)
    repository.soft_delete_exercise(first.id)

    second = repository.create_exercise("Yoga", "movilidad", _D, _D)
    assert second.id != first.id
    assert second.name == "Yoga"


@pytest.mark.integration
def test_create_catalog_exercise_normalizes_name(db, db_user):
    created = repository.create_exercise("  press   banca ", None, _D, _D)

    assert created.name == "Press banca"


@pytest.mark.integration
def test_update_catalog_exercise(db, db_user):
    created = repository.create_exercise("Remo", "espalda", _D, _D)

    ok = repository.update_exercise(created.id, name="Remo invertido", kind=None)
    assert ok is True

    updated = repository.get_exercise_by_id(created.id)
    assert updated.name == "Remo invertido"
    assert updated.kind is None


@pytest.mark.integration
def test_update_catalog_exercise_no_fields(db, db_user):
    created = repository.create_exercise("Remo", None, _D, _D)
    assert repository.update_exercise(created.id) is True


@pytest.mark.integration
def test_update_catalog_exercise_invalid_column(db, db_user):
    created = repository.create_exercise("Remo", None, _D, _D)
    with pytest.raises(ValueError):
        repository.update_exercise(created.id, hacker_column="x")


@pytest.mark.integration
def test_update_catalog_exercise_missing_row(db, db_user):
    assert repository.update_exercise(9999, name="X") is False


# -- Weight Entries --


@pytest.mark.integration
def test_upsert_weight_entry_creates(db, db_user, frozen_today):
    entry = repository.upsert_weight_entry(_USER_ID, 80.5, None, _D, _D)

    assert entry.id > 0
    assert entry.user_id == _USER_ID
    assert entry.weight_kg == 80.5
    assert entry.measured_at == _D
    assert entry.notes is None
    assert entry.created_at == _D


@pytest.mark.integration
def test_upsert_weight_entry_updates_same_date(db, db_user):
    repository.upsert_weight_entry(_USER_ID, 80.5, None, _D, _D)
    updated = repository.upsert_weight_entry(_USER_ID, 81.2, "post workout", _D, _D)

    entries = repository.get_weight_entries(_USER_ID)
    assert len(entries) == 1
    assert updated.weight_kg == 81.2
    assert updated.notes == "post workout"


@pytest.mark.integration
def test_upsert_weight_entry_scoped_per_user(db, db_user, db_second_user):
    repository.upsert_weight_entry(1, 80.0, None, _D, _D)
    repository.upsert_weight_entry(2, 65.0, None, _D, _D)

    first = repository.get_weight_entries(1)
    second = repository.get_weight_entries(2)

    assert first[0].weight_kg == 80.0
    assert second[0].weight_kg == 65.0


@pytest.mark.integration
def test_get_weight_entry_by_user_and_date(db, db_user):
    repository.upsert_weight_entry(_USER_ID, 80.0, None, _D, _D)

    found = repository.get_weight_entry_by_user_and_date(_USER_ID, _D)
    assert found is not None
    assert found.weight_kg == 80.0

    assert repository.get_weight_entry_by_user_and_date(_USER_ID, "2026-03-16") is None
    assert repository.get_weight_entry_by_user_and_date(999, _D) is None


@pytest.mark.integration
def test_get_weight_entry_by_id_and_user(db, db_user):
    created = repository.upsert_weight_entry(_USER_ID, 80.0, None, _D, _D)

    found = repository.get_weight_entry_by_id_and_user(created.id, _USER_ID)
    assert found is not None

    assert repository.get_weight_entry_by_id_and_user(created.id, 999) is None
    assert repository.get_weight_entry_by_id_and_user(9999, _USER_ID) is None


@pytest.mark.integration
def test_get_weight_entries_with_date_filters(db, db_user):
    repository.upsert_weight_entry(_USER_ID, 80.0, None, "2026-03-01", _D)
    repository.upsert_weight_entry(_USER_ID, 79.5, None, "2026-03-10", _D)
    repository.upsert_weight_entry(_USER_ID, 79.0, None, "2026-03-20", _D)

    assert len(repository.get_weight_entries(_USER_ID)) == 3

    between = repository.get_weight_entries(_USER_ID, "2026-03-05", "2026-03-15")
    assert len(between) == 1
    assert between[0].weight_kg == 79.5

    from_only = repository.get_weight_entries(_USER_ID, from_date="2026-03-10")
    assert len(from_only) == 2

    to_only = repository.get_weight_entries(_USER_ID, to_date="2026-03-10")
    assert len(to_only) == 2


@pytest.mark.integration
def test_get_latest_weight_before(db, db_user):
    repository.upsert_weight_entry(_USER_ID, 82.0, None, "2026-02-01", _D)
    repository.upsert_weight_entry(_USER_ID, 80.0, None, "2026-03-14", _D)

    latest = repository.get_latest_weight_before(_USER_ID, _D)
    assert latest is not None
    assert latest.weight_kg == 80.0

    assert repository.get_latest_weight_before(_USER_ID, "2026-01-15") is None
    assert repository.get_latest_weight_before(999, _D) is None


@pytest.mark.integration
def test_delete_weight_entry(db, db_user):
    created = repository.upsert_weight_entry(_USER_ID, 80.0, None, _D, _D)

    assert repository.delete_weight_entry(created.id, 999) is False
    assert repository.delete_weight_entry(created.id, _USER_ID) is True
    assert repository.get_weight_entry_by_id_and_user(created.id, _USER_ID) is None
    assert repository.delete_weight_entry(created.id, _USER_ID) is False


@pytest.mark.integration
def test_update_weight_entry_fields(db, db_user):
    created = repository.upsert_weight_entry(_USER_ID, 80.0, None, _D, _D)

    assert (
        repository.update_weight_entry(created.id, _USER_ID, weight_kg=79.25, notes="ayuno") is True
    )

    updated = repository.get_weight_entry_by_id_and_user(created.id, _USER_ID)
    assert updated is not None
    assert updated.weight_kg == 79.25
    assert updated.notes == "ayuno"
    assert updated.measured_at == _D
    assert updated.created_at == created.created_at


@pytest.mark.integration
def test_update_weight_entry_measured_at(db, db_user):
    created = repository.upsert_weight_entry(_USER_ID, 80.0, None, _D, _D)

    assert repository.update_weight_entry(created.id, _USER_ID, measured_at="2026-03-20") is True

    updated = repository.get_weight_entry_by_id_and_user(created.id, _USER_ID)
    assert updated is not None
    assert updated.measured_at == "2026-03-20"
    assert repository.get_weight_entry_by_user_and_date(_D, _USER_ID) is None


@pytest.mark.integration
def test_update_weight_entry_clears_notes(db, db_user):
    created = repository.upsert_weight_entry(_USER_ID, 80.0, "ayuno", _D, _D)

    assert repository.update_weight_entry(created.id, _USER_ID, notes=None) is True

    updated = repository.get_weight_entry_by_id_and_user(created.id, _USER_ID)
    assert updated is not None
    assert updated.notes is None


@pytest.mark.integration
def test_update_weight_entry_no_fields(db, db_user):
    created = repository.upsert_weight_entry(_USER_ID, 80.0, None, _D, _D)

    assert repository.update_weight_entry(created.id, _USER_ID) is True


@pytest.mark.integration
def test_update_weight_entry_invalid_column(db, db_user):
    with pytest.raises(ValueError):
        repository.update_weight_entry(1, _USER_ID, hacker_column="x")


@pytest.mark.integration
def test_update_weight_entry_missing_row_or_not_owned(db, db_user):
    created = repository.upsert_weight_entry(_USER_ID, 80.0, None, _D, _D)

    assert repository.update_weight_entry(9999, _USER_ID, weight_kg=75.0) is False
    assert repository.update_weight_entry(created.id, 999, weight_kg=75.0) is False


@pytest.mark.integration
def test_update_weight_entry_unique_date_conflict(db, db_user):
    first = repository.upsert_weight_entry(_USER_ID, 80.0, None, _D, _D)
    repository.upsert_weight_entry(_USER_ID, 75.0, None, "2026-03-10", _D)

    with pytest.raises(WeightEntryDateConflictError) as exc_info:
        repository.update_weight_entry(first.id, _USER_ID, measured_at="2026-03-10")

    conflict = repository.get_weight_entry_by_user_and_date(_USER_ID, "2026-03-10")
    assert exc_info.value.weight_entry.id == conflict.id
    assert conflict.weight_kg == 75.0


# -- Workout Entries --


@pytest.mark.integration
def test_create_workout_entry_full(db, db_user):
    exercise = repository.create_exercise("correr", None, _D, _D)
    entry = repository.create_workout_entry(
        _USER_ID, exercise.id, None, 45, 450.5, [], {}, "5km", _D, _D
    )

    assert entry.exercise_id == exercise.id
    assert entry.duration_min == 45
    assert entry.calories_burned == 450.5
    assert entry.sets_breakdown == []
    assert entry.metrics == {}
    assert entry.performed_at == _D
    assert entry.notes == "5km"


@pytest.mark.integration
def test_create_workout_entry_optionals_null(db, db_user):
    exercise = repository.create_exercise("yoga", None, _D, _D)
    entry = repository.create_workout_entry(
        _USER_ID, exercise.id, None, 60, None, [], None, None, _D, _D
    )

    assert entry.duration_min == 60
    assert entry.calories_burned is None
    assert entry.sets_breakdown == []
    assert entry.metrics == {}
    assert entry.notes is None


@pytest.mark.integration
def test_create_workout_entry_sets_roundtrip(db, db_user):
    exercise = repository.create_exercise("press banca", None, _D, _D)
    rows = [
        {"exercise_id": None, "exercise_name": "press", "weight_kg": 60.5, "reps": 8, "sets": 3},
        {"exercise_id": None, "exercise_name": "Press", "weight_kg": None, "reps": 12, "sets": 2},
    ]
    created = repository.create_workout_entry(
        _USER_ID, exercise.id, None, None, None, rows, {}, None, _D, _D
    )

    assert created.duration_min is None
    assert created.sets_breakdown == rows

    found = repository.get_workout_entry_by_id_and_user(created.id, _USER_ID)
    assert found is not None
    assert found.sets_breakdown == rows


@pytest.mark.integration
def test_update_workout_entry_sets_breakdown(db, db_user):
    exercise = repository.create_exercise("press banca", None, _D, _D)
    created = repository.create_workout_entry(
        _USER_ID,
        exercise.id,
        None,
        30,
        None,
        [{"exercise_id": None, "exercise_name": "Press", "weight_kg": 50.0, "reps": 8, "sets": 1}],
        {},
        None,
        _D,
        _D,
    )

    ok = repository.update_workout_entry(
        created.id,
        _USER_ID,
        duration_min=None,
        sets_breakdown=[
            {"exercise_id": None, "exercise_name": "press", "weight_kg": 70, "reps": 6, "sets": 4}
        ],
    )
    assert ok is True

    updated = repository.get_workout_entry_by_id_and_user(created.id, _USER_ID)
    assert updated is not None
    assert updated.duration_min is None
    assert updated.sets_breakdown == [
        {"exercise_id": None, "exercise_name": "press", "weight_kg": 70, "reps": 6, "sets": 4}
    ]

    ok = repository.update_workout_entry(created.id, _USER_ID, sets_breakdown=[])
    assert ok is True

    cleared = repository.get_workout_entry_by_id_and_user(created.id, _USER_ID)
    assert cleared is not None
    assert cleared.sets_breakdown == []


@pytest.mark.integration
def test_get_workout_entry_by_id_and_user(db, db_user):
    exercise = repository.create_exercise("correr", None, _D, _D)
    created = repository.create_workout_entry(
        _USER_ID, exercise.id, None, 45, 450.5, [], {}, "5km", _D, _D
    )

    found = repository.get_workout_entry_by_id_and_user(created.id, _USER_ID)
    assert found is not None
    assert found.exercise_id == exercise.id

    assert repository.get_workout_entry_by_id_and_user(created.id, 999) is None
    assert repository.get_workout_entry_by_id_and_user(9999, _USER_ID) is None


@pytest.mark.integration
def test_get_workout_entries_filters(db, db_user, db_second_user):
    correr = repository.create_exercise("correr", None, _D, _D)
    gym = repository.create_exercise("gym", None, _D, _D)
    repository.create_workout_entry(
        _USER_ID, correr.id, None, 30, None, [], {}, None, "2026-03-01", _D
    )
    repository.create_workout_entry(
        _USER_ID, gym.id, None, 60, None, [], {}, None, "2026-03-10", _D
    )
    repository.create_workout_entry(
        _USER_ID, correr.id, None, 40, None, [], {}, None, "2026-03-20", _D
    )
    repository.create_workout_entry(
        2, correr.id, None, 50, None, [], {}, None, "2026-03-20", _D
    )

    own = repository.get_workout_entries(_USER_ID)
    assert len(own) == 3
    assert own[0].performed_at == "2026-03-20"

    by_exercise = repository.get_workout_entries(_USER_ID, exercise_id=correr.id)
    assert len(by_exercise) == 2

    windowed = repository.get_workout_entries(
        _USER_ID, from_date="2026-03-05", to_date="2026-03-15"
    )
    assert len(windowed) == 1
    assert windowed[0].exercise_id == gym.id

    limited = repository.get_workout_entries(_USER_ID, limit=1)
    assert len(limited) == 1

    other = repository.get_workout_entries(2)
    assert len(other) == 1


@pytest.mark.integration
def test_update_workout_entry_fields(db, db_user):
    correr = repository.create_exercise("correr", None, _D, _D)
    natacion = repository.create_exercise("natación", None, _D, _D)
    created = repository.create_workout_entry(
        _USER_ID, correr.id, None, 30, 300, [], {}, None, _D, _D
    )

    ok = repository.update_workout_entry(
        created.id,
        _USER_ID,
        exercise_id=natacion.id,
        duration_min=50,
        calories_burned=None,
        performed_at="2026-03-16",
        notes="pool",
    )
    assert ok is True

    updated = repository.get_workout_entry_by_id_and_user(created.id, _USER_ID)
    assert updated.exercise_id == natacion.id
    assert updated.duration_min == 50
    assert updated.calories_burned is None
    assert updated.performed_at == "2026-03-16"
    assert updated.notes == "pool"


@pytest.mark.integration
def test_update_workout_entry_no_fields(db, db_user):
    exercise = repository.create_exercise("correr", None, _D, _D)
    created = repository.create_workout_entry(
        _USER_ID, exercise.id, None, 30, None, [], {}, None, _D, _D
    )
    assert repository.update_workout_entry(created.id, _USER_ID) is True


@pytest.mark.integration
def test_create_and_update_workout_entry_metrics(db, db_user):
    exercise = repository.create_exercise("gym", None, _D, _D)
    created = repository.create_workout_entry(
        _USER_ID,
        exercise.id,
        None,
        60,
        None,
        [],
        {"rpe": 8},
        None,
        _D,
        _D,
    )
    assert created.metrics == {"rpe": 8}

    ok = repository.update_workout_entry(created.id, _USER_ID, metrics={"distance_km": 5})
    assert ok is True

    updated = repository.get_workout_entry_by_id_and_user(created.id, _USER_ID)
    assert updated.metrics == {"distance_km": 5}


@pytest.mark.integration
def test_update_workout_entry_invalid_column(db, db_user):
    exercise = repository.create_exercise("correr", None, _D, _D)
    created = repository.create_workout_entry(
        _USER_ID, exercise.id, None, 30, None, [], {}, None, _D, _D
    )

    with pytest.raises(ValueError):
        repository.update_workout_entry(created.id, _USER_ID, hacker_column="x")


@pytest.mark.integration
def test_update_workout_entry_not_owned(db, db_user):
    exercise = repository.create_exercise("correr", None, _D, _D)
    created = repository.create_workout_entry(
        _USER_ID, exercise.id, None, 30, None, [], {}, None, _D, _D
    )
    assert repository.update_workout_entry(created.id, 999, duration_min=99) is False


@pytest.mark.integration
def test_delete_workout_entry(db, db_user):
    exercise = repository.create_exercise("correr", None, _D, _D)
    created = repository.create_workout_entry(
        _USER_ID, exercise.id, None, 30, None, [], {}, None, _D, _D
    )

    assert repository.delete_workout_entry(created.id, 999) is False
    assert repository.delete_workout_entry(created.id, _USER_ID) is True
    assert repository.get_workout_entry_by_id_and_user(created.id, _USER_ID) is None


# -- Routines --


@pytest.mark.integration
def test_create_and_get_catalog_routine(db, db_user):
    created = repository.create_routine("Push day", "fuerza", "pecho y triceps", _D, _D)

    assert created.id > 0
    assert created.name == "Push day"
    assert created.category == "fuerza"
    assert created.description == "pecho y triceps"
    assert created.created_at == _D
    assert created.updated_at == _D
    assert created.deleted_at is None

    found = repository.get_routine_by_id(created.id)
    assert found is not None
    assert found.name == "Push day"

    by_name = repository.get_active_routine_by_name("push day")
    assert by_name is not None
    assert by_name.id == created.id

    by_name = repository.get_active_routine_by_name("PUSH DAY")
    assert by_name is not None
    assert by_name.id == created.id

    assert repository.get_active_routine_by_name("Leg day") is None


@pytest.mark.integration
def test_create_routine_unique_name(db, db_user):
    repository.create_routine("Rutina A", None, None, _D, _D)

    with pytest.raises(RoutineAlreadyExistsError):
        repository.create_routine("Rutina A", "fuerza", None, _D, _D)

    with pytest.raises(RoutineAlreadyExistsError):
        repository.create_routine("rutina a", "fuerza", None, _D, _D)


@pytest.mark.integration
def test_create_routine_normalizes_name(db, db_user):
    created = repository.create_routine("  rutina   push  ", None, None, _D, _D)

    assert created.name == "Rutina push"


@pytest.mark.integration
def test_get_routines_orders_by_name(db, db_user):
    repository.create_routine("zumba", None, None, _D, _D)
    repository.create_routine("abdominales", None, None, _D, _D)
    repository.create_routine("correr", None, None, _D, _D)

    names = [r.name for r in repository.get_routines()]

    assert names == ["Abdominales", "Correr", "Zumba"]


@pytest.mark.integration
def test_soft_delete_routine_hides_from_default_queries(db, db_user):
    created = repository.create_routine("Yoga", None, None, _D, _D)

    assert repository.soft_delete_routine(created.id) is True
    assert repository.soft_delete_routine(created.id) is False
    assert repository.get_routine_by_id(created.id) is None
    assert repository.get_active_routine_by_name("yoga") is None
    assert len(repository.get_routines()) == 0

    deleted = repository.get_routines(include_deleted=True)
    assert len(deleted) == 1
    assert deleted[0].deleted_at is not None


@pytest.mark.integration
def test_routine_name_reusable_after_soft_delete(db, db_user):
    first = repository.create_routine("Yoga", None, None, _D, _D)
    repository.soft_delete_routine(first.id)

    second = repository.create_routine("Yoga", "movilidad", None, _D, _D)
    assert second.id != first.id
    assert second.name == "Yoga"


@pytest.mark.integration
def test_update_routine(db, db_user):
    created = repository.create_routine("Remo", "espalda", "remadas", _D, _D)

    ok = repository.update_routine(
        created.id, name="Remo invertido", category=None, description="x"
    )
    assert ok is True

    updated = repository.get_routine_by_id(created.id)
    assert updated.name == "Remo invertido"
    assert updated.category is None
    assert updated.description == "x"


@pytest.mark.integration
def test_update_routine_no_fields(db, db_user):
    created = repository.create_routine("Remo", None, None, _D, _D)
    assert repository.update_routine(created.id) is True


@pytest.mark.integration
def test_update_routine_invalid_column(db, db_user):
    created = repository.create_routine("Remo", None, None, _D, _D)
    with pytest.raises(ValueError):
        repository.update_routine(created.id, hacker_column="x")


@pytest.mark.integration
def test_update_routine_missing_row(db, db_user):
    assert repository.update_routine(9999, name="X") is False


@pytest.mark.integration
def test_update_routine_unique_name_conflict(db, db_user):
    repository.create_routine("Rutina A", None, None, _D, _D)
    other = repository.create_routine("Rutina B", None, None, _D, _D)

    with pytest.raises(RoutineAlreadyExistsError):
        repository.update_routine(other.id, name="Rutina A")


@pytest.mark.integration
def test_update_exercise_unique_name_conflict(db, db_user):
    repository.create_exercise("Press banca", None, _D, _D)
    remo = repository.create_exercise("Remo", None, _D, _D)

    with pytest.raises(ExerciseAlreadyExistsError):
        repository.update_exercise(remo.id, name="Press banca")


@pytest.mark.integration
def test_set_routine_exercises_roundtrip(db, db_user):
    sentadilla = repository.create_exercise("sentadilla", None, _D, _D)
    press = repository.create_exercise("press banca", None, _D, _D)
    routine = repository.create_routine("Push", None, None, _D, _D)

    rows = repository.set_routine_exercises(
        routine.id,
        [
            {"exercise_id": sentadilla.id, "weight_kg": 80.5, "reps": 10, "sets": 4, "position": 0},
            {"exercise_id": press.id, "weight_kg": 50.0, "reps": 8, "sets": 3, "position": 1},
        ],
    )

    assert [re.exercise_id for re in rows] == [sentadilla.id, press.id]
    assert rows[0].position == 0
    assert rows[0].weight_kg == 80.5
    assert rows[1].weight_kg == 50.0

    found = repository.get_routine_exercises(routine.id)
    assert [re.exercise_id for re in found] == [sentadilla.id, press.id]
    assert [re.reps for re in found] == [10, 8]
    assert [re.sets for re in found] == [4, 3]

    replaced = repository.set_routine_exercises(
        routine.id,
        [{"exercise_id": press.id, "weight_kg": None, "reps": 12, "sets": 5, "position": 0}],
    )
    assert len(replaced) == 1
    assert replaced[0].exercise_id == press.id
    assert replaced[0].weight_kg is None

    remaining = repository.get_routine_exercises(routine.id)
    assert len(remaining) == 1
    assert remaining[0].exercise_id == press.id


@pytest.mark.integration
def test_get_routine_exercises_by_ids(db, db_user):
    sentadilla = repository.create_exercise("sentadilla", None, _D, _D)
    press = repository.create_exercise("press banca", None, _D, _D)
    r1 = repository.create_routine("Push", None, None, _D, _D)
    r2 = repository.create_routine("Pull", None, None, _D, _D)

    repository.set_routine_exercises(
        r1.id, [{"exercise_id": press.id, "weight_kg": None, "reps": 8, "sets": 3, "position": 0}]
    )
    repository.set_routine_exercises(
        r2.id,
        [{"exercise_id": sentadilla.id, "weight_kg": None, "reps": 10, "sets": 4, "position": 0}],
    )

    grouped = repository.get_routine_exercises_by_ids([r1.id, r2.id])
    assert set(grouped.keys()) == {r1.id, r2.id}
    assert grouped[r1.id][0].exercise_id == press.id
    assert grouped[r2.id][0].exercise_id == sentadilla.id

    assert repository.get_routine_exercises_by_ids([]) == {}
