import pytest

import modules.fitness.repository as repository

_D = "2026-03-15"
_USER_ID = 1


@pytest.mark.integration
def test_upsert_weight_entry_creates(db, db_user, frozen_today):
    entry = repository.upsert_weight_entry(_USER_ID, 80.5, _D, None, _D)

    assert entry.id > 0
    assert entry.user_id == _USER_ID
    assert entry.weight_kg == 80.5
    assert entry.measured_at == _D
    assert entry.notes is None
    assert entry.created_at == _D


@pytest.mark.integration
def test_upsert_weight_entry_updates_same_date(db, db_user):
    repository.upsert_weight_entry(_USER_ID, 80.5, _D, None, _D)
    updated = repository.upsert_weight_entry(_USER_ID, 81.2, _D, "post workout", _D)

    entries = repository.get_weight_entries(_USER_ID)
    assert len(entries) == 1
    assert updated.weight_kg == 81.2
    assert updated.notes == "post workout"


@pytest.mark.integration
def test_upsert_weight_entry_scoped_per_user(db, db_user, db_second_user):
    repository.upsert_weight_entry(1, 80.0, _D, None, _D)
    repository.upsert_weight_entry(2, 65.0, _D, None, _D)

    first = repository.get_weight_entries(1)
    second = repository.get_weight_entries(2)

    assert first[0].weight_kg == 80.0
    assert second[0].weight_kg == 65.0


@pytest.mark.integration
def test_get_weight_entry_by_date_and_user(db, db_user):
    repository.upsert_weight_entry(_USER_ID, 80.0, _D, None, _D)

    found = repository.get_weight_entry_by_date_and_user(_D, _USER_ID)
    assert found is not None
    assert found.weight_kg == 80.0

    assert repository.get_weight_entry_by_date_and_user("2026-03-16", _USER_ID) is None
    assert repository.get_weight_entry_by_date_and_user(_D, 999) is None


@pytest.mark.integration
def test_get_weight_entry_by_id_and_user(db, db_user):
    created = repository.upsert_weight_entry(_USER_ID, 80.0, _D, None, _D)

    found = repository.get_weight_entry_by_id_and_user(created.id, _USER_ID)
    assert found is not None

    assert repository.get_weight_entry_by_id_and_user(created.id, 999) is None
    assert repository.get_weight_entry_by_id_and_user(9999, _USER_ID) is None


@pytest.mark.integration
def test_get_weight_entries_with_date_filters(db, db_user):
    repository.upsert_weight_entry(_USER_ID, 80.0, "2026-03-01", None, _D)
    repository.upsert_weight_entry(_USER_ID, 79.5, "2026-03-10", None, _D)
    repository.upsert_weight_entry(_USER_ID, 79.0, "2026-03-20", None, _D)

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
    repository.upsert_weight_entry(_USER_ID, 82.0, "2026-02-01", None, _D)
    repository.upsert_weight_entry(_USER_ID, 80.0, "2026-03-14", None, _D)

    latest = repository.get_latest_weight_before(_USER_ID, _D)
    assert latest is not None
    assert latest.weight_kg == 80.0

    assert repository.get_latest_weight_before(_USER_ID, "2026-01-15") is None
    assert repository.get_latest_weight_before(999, _D) is None


@pytest.mark.integration
def test_delete_weight_entry(db, db_user):
    created = repository.upsert_weight_entry(_USER_ID, 80.0, _D, None, _D)

    assert repository.delete_weight_entry(created.id, 999) is False
    assert repository.delete_weight_entry(created.id, _USER_ID) is True
    assert repository.get_weight_entry_by_id_and_user(created.id, _USER_ID) is None
    assert repository.delete_weight_entry(created.id, _USER_ID) is False


# -- Exercise Entries --


@pytest.mark.integration
def test_create_exercise_entry_full(db, db_user):
    entry = repository.create_exercise_entry(
        _USER_ID, "correr", 45, "high", 450.5, _D, "5km", _D
    )

    assert entry.exercise_type == "correr"
    assert entry.duration_min == 45
    assert entry.intensity == "high"
    assert entry.calories_burned == 450.5
    assert entry.performed_at == _D
    assert entry.notes == "5km"


@pytest.mark.integration
def test_create_exercise_entry_optionals_null(db, db_user):
    entry = repository.create_exercise_entry(_USER_ID, "yoga", 60, None, None, _D, None, _D)

    assert entry.intensity is None
    assert entry.calories_burned is None
    assert entry.notes is None


@pytest.mark.integration
def test_get_exercise_entry_by_id_and_user(db, db_user):
    created = repository.create_exercise_entry(
        _USER_ID, "correr", 45, "high", 450.5, _D, "5km", _D
    )

    found = repository.get_exercise_entry_by_id_and_user(created.id, _USER_ID)
    assert found is not None
    assert found.intensity == "high"

    assert repository.get_exercise_entry_by_id_and_user(created.id, 999) is None
    assert repository.get_exercise_entry_by_id_and_user(9999, _USER_ID) is None


@pytest.mark.integration
def test_get_exercise_entries_filters(db, db_user, db_second_user):
    repository.create_exercise_entry(_USER_ID, "correr", 30, None, None, "2026-03-01", None, _D)
    repository.create_exercise_entry(_USER_ID, "gym", 60, None, None, "2026-03-10", None, _D)
    repository.create_exercise_entry(_USER_ID, "correr", 40, None, None, "2026-03-20", None, _D)
    repository.create_exercise_entry(2, "correr", 50, None, None, "2026-03-20", None, _D)

    own = repository.get_exercise_entries(_USER_ID)
    assert len(own) == 3
    assert own[0].performed_at == "2026-03-20"

    by_type = repository.get_exercise_entries(_USER_ID, exercise_type="correr")
    assert len(by_type) == 2

    windowed = repository.get_exercise_entries(
        _USER_ID, from_date="2026-03-05", to_date="2026-03-15"
    )
    assert len(windowed) == 1
    assert windowed[0].exercise_type == "gym"

    limited = repository.get_exercise_entries(_USER_ID, limit=1)
    assert len(limited) == 1

    other = repository.get_exercise_entries(2)
    assert len(other) == 1


@pytest.mark.integration
def test_update_exercise_entry_fields(db, db_user):
    created = repository.create_exercise_entry(
        _USER_ID, "correr", 30, "low", 300, _D, None, _D
    )

    ok = repository.update_exercise_entry(
        created.id,
        _USER_ID,
        exercise_type="natación",
        duration_min=50,
        intensity="medium",
        calories_burned=None,
        performed_at="2026-03-16",
        notes="pool",
    )
    assert ok is True

    updated = repository.get_exercise_entry_by_id_and_user(created.id, _USER_ID)
    assert updated.exercise_type == "natación"
    assert updated.duration_min == 50
    assert updated.intensity == "medium"
    assert updated.calories_burned is None
    assert updated.performed_at == "2026-03-16"
    assert updated.notes == "pool"


@pytest.mark.integration
def test_update_exercise_entry_no_fields(db, db_user):
    created = repository.create_exercise_entry(
        _USER_ID, "correr", 30, None, None, _D, None, _D
    )
    assert repository.update_exercise_entry(created.id, _USER_ID) is True


@pytest.mark.integration
def test_update_exercise_entry_invalid_column(db, db_user):
    with pytest.raises(ValueError):
        repository.update_exercise_entry(1, _USER_ID, hacker_column="x")


@pytest.mark.integration
def test_update_exercise_entry_not_owned(db, db_user):
    created = repository.create_exercise_entry(
        _USER_ID, "correr", 30, None, None, _D, None, _D
    )
    assert repository.update_exercise_entry(created.id, 999, duration_min=99) is False


@pytest.mark.integration
def test_delete_exercise_entry(db, db_user):
    created = repository.create_exercise_entry(
        _USER_ID, "correr", 30, None, None, _D, None, _D
    )

    assert repository.delete_exercise_entry(created.id, 999) is False
    assert repository.delete_exercise_entry(created.id, _USER_ID) is True
    assert repository.get_exercise_entry_by_id_and_user(created.id, _USER_ID) is None
