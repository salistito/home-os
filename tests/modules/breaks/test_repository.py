import pytest

import modules.breaks.repository as repository
import modules.users.repository as users_repository


@pytest.fixture
def break_user(db):
    return users_repository.create_user("Break User")


@pytest.fixture
def break_user2(db):
    return users_repository.create_user("Break User 2")


@pytest.mark.integration
def test_create_break_period(db, break_user):
    period = repository.create_break_period(
        "Vacaciones", "2026-03-10", "2026-03-20", "2026-03-01", [break_user.id], ["tasks", "food"]
    )

    assert period.id > 0
    assert period.label == "Vacaciones"
    assert period.start_date == "2026-03-10"
    assert period.end_date == "2026-03-20"
    assert period.user_ids == [break_user.id]
    assert set(period.modules) == {"tasks", "food"}


@pytest.mark.integration
def test_create_break_period_open_ended(db, break_user):
    period = repository.create_break_period(
        None, "2026-03-10", None, "2026-03-01", [break_user.id], ["tasks"]
    )

    assert period.label is None
    assert period.end_date is None


@pytest.mark.integration
def test_get_break_period_by_id_missing(db):
    assert repository.get_break_period_by_id(9999) is None


@pytest.mark.integration
def test_get_break_periods_orders_by_start_date_desc(db, break_user):
    repository.create_break_period(
        "Later", "2026-04-01", None, "2026-03-01", [break_user.id], ["tasks"]
    )
    repository.create_break_period(
        "Earlier", "2026-02-01", None, "2026-03-01", [break_user.id], ["tasks"]
    )

    periods = repository.get_break_periods()

    assert [p.label for p in periods] == ["Later", "Earlier"]


@pytest.mark.integration
def test_update_break_period(db, break_user):
    period = repository.create_break_period(
        "Old", "2026-03-10", None, "2026-03-01", [break_user.id], ["tasks"]
    )

    repository.update_break_period(period.id, label="New", end_date="2026-03-25")

    updated = repository.get_break_period_by_id(period.id)
    assert updated.label == "New"
    assert updated.end_date == "2026-03-25"
    assert updated.start_date == "2026-03-10"


@pytest.mark.integration
def test_set_break_period_user_ids_replaces(db, break_user, break_user2):
    period = repository.create_break_period(
        "Test", "2026-03-10", None, "2026-03-01", [break_user.id], ["tasks"]
    )

    repository.set_break_period_user_ids(period.id, [break_user.id, break_user2.id])

    updated = repository.get_break_period_by_id(period.id)
    assert set(updated.user_ids) == {break_user.id, break_user2.id}


@pytest.mark.integration
def test_set_break_period_modules_replaces(db, break_user):
    period = repository.create_break_period(
        "Test", "2026-03-10", None, "2026-03-01", [break_user.id], ["tasks"]
    )

    repository.set_break_period_modules(period.id, ["food", "fitness"])

    updated = repository.get_break_period_by_id(period.id)
    assert set(updated.modules) == {"food", "fitness"}


@pytest.mark.integration
def test_delete_break_period(db, break_user):
    period = repository.create_break_period(
        "Test", "2026-03-10", None, "2026-03-01", [break_user.id], ["tasks"]
    )

    assert repository.delete_break_period(period.id) is True
    assert repository.get_break_period_by_id(period.id) is None


@pytest.mark.integration
def test_delete_break_period_missing(db):
    assert repository.delete_break_period(9999) is False


@pytest.mark.integration
def test_get_break_periods_user_ids(db, break_user, break_user2):
    repository.create_break_period(
        "A", "2026-03-10", None, "2026-03-01", [break_user.id], ["tasks"]
    )
    repository.create_break_period(
        "B", "2026-04-01", "2026-04-10", "2026-03-01", [break_user2.id], ["food"]
    )

    assert repository.get_break_periods_user_ids("2026-03-15", "tasks") == {break_user.id}
    assert repository.get_break_periods_user_ids("2026-03-15", "food") == set()
    assert repository.get_break_periods_user_ids("2026-03-09", "tasks") == set()
    assert repository.get_break_periods_user_ids("2026-04-05", "tasks") == {break_user.id}
    assert repository.get_break_periods_user_ids("2026-04-05", "food") == {break_user2.id}
    assert repository.get_break_periods_user_ids("2026-04-05", "bogus") == set()
    assert repository.get_break_periods_user_ids("2026-04-11", "tasks") == {break_user.id}


@pytest.mark.integration
def test_get_break_periods_in_range_overlap(db, break_user):
    repository.create_break_period(
        "Vacaciones", "2026-03-10", "2026-03-20", "2026-03-01", [break_user.id], ["tasks"]
    )
    repository.create_break_period(
        "Pasado", "2026-01-01", "2026-01-31", "2026-03-01", [break_user.id], ["tasks"]
    )
    repository.create_break_period(
        "Futuro", "2026-05-01", None, "2026-03-01", [break_user.id], ["tasks"]
    )

    inside = repository.get_break_periods_in_range(break_user.id, "2026-03-15", "2026-03-16")
    assert [p.label for p in inside] == ["Vacaciones"]

    spanning = repository.get_break_periods_in_range(
        break_user.id, "2026-03-01", "2026-03-31"
    )
    assert [p.label for p in spanning] == ["Vacaciones"]

    no_overlap = repository.get_break_periods_in_range(
        break_user.id, "2026-02-01", "2026-02-28"
    )
    assert no_overlap == []


@pytest.mark.integration
def test_get_break_periods_in_range_boundaries_are_inclusive(db, break_user):
    repository.create_break_period(
        "Vacaciones", "2026-03-10", "2026-03-20", "2026-03-01", [break_user.id], ["tasks"]
    )

    starts_on_from = repository.get_break_periods_in_range(
        break_user.id, "2026-03-10", "2026-03-10"
    )
    ends_on_to = repository.get_break_periods_in_range(
        break_user.id, "2026-03-20", "2026-03-20"
    )
    before = repository.get_break_periods_in_range(break_user.id, "2026-03-09", "2026-03-09")
    after = repository.get_break_periods_in_range(break_user.id, "2026-03-21", "2026-03-21")

    assert [p.label for p in starts_on_from] == ["Vacaciones"]
    assert [p.label for p in ends_on_to] == ["Vacaciones"]
    assert before == []
    assert after == []


@pytest.mark.integration
def test_get_break_periods_in_range_open_ended_covers_range(db, break_user):
    repository.create_break_period(
        "Indefinido", "2026-03-10", None, "2026-03-01", [break_user.id], ["tasks"]
    )

    future_range = repository.get_break_periods_in_range(
        break_user.id, "2027-01-01", "2027-01-07"
    )
    before_start = repository.get_break_periods_in_range(
        break_user.id, "2026-03-01", "2026-03-09"
    )

    assert [p.label for p in future_range] == ["Indefinido"]
    assert before_start == []


@pytest.mark.integration
def test_get_break_periods_in_range_orders_by_start_date_asc(db, break_user):
    repository.create_break_period(
        "Puente", "2026-03-14", "2026-03-16", "2026-03-01", [break_user.id], ["tasks"]
    )
    repository.create_break_period(
        "Vacaciones", "2026-03-10", "2026-03-20", "2026-03-01", [break_user.id], ["tasks"]
    )

    periods = repository.get_break_periods_in_range(break_user.id, "2026-03-15", "2026-03-15")

    assert [p.label for p in periods] == ["Vacaciones", "Puente"]


@pytest.mark.integration
def test_get_break_periods_in_range_isolates_user_and_module(db, break_user, break_user2):
    repository.create_break_period(
        "Comida", "2026-03-10", None, "2026-03-01", [break_user.id], ["food"]
    )
    repository.create_break_period(
        "Tareas", "2026-03-10", None, "2026-03-01", [break_user.id], ["tasks"]
    )
    repository.create_break_period(
        "Otro", "2026-03-10", None, "2026-03-01", [break_user2.id], ["food"]
    )

    no_module = repository.get_break_periods_in_range(
        break_user.id, "2026-03-15", "2026-03-15"
    )
    food = repository.get_break_periods_in_range(
        break_user.id, "2026-03-15", "2026-03-15", "food"
    )
    tasks = repository.get_break_periods_in_range(
        break_user.id, "2026-03-15", "2026-03-15", "tasks"
    )
    other_user = repository.get_break_periods_in_range(
        break_user2.id, "2026-03-15", "2026-03-15", "food"
    )
    unknown_user = repository.get_break_periods_in_range(9999, "2026-03-15", "2026-03-15")

    assert {p.label for p in no_module} == {"Comida", "Tareas"}
    assert [p.label for p in food] == ["Comida"]
    assert [p.label for p in tasks] == ["Tareas"]
    assert [p.label for p in other_user] == ["Otro"]
    assert unknown_user == []
