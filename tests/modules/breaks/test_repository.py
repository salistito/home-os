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
        "Vacaciones", "2026-03-10", "2026-03-20", "2026-03-01", [break_user.id]
    )

    assert period.id > 0
    assert period.label == "Vacaciones"
    assert period.start_date == "2026-03-10"
    assert period.end_date == "2026-03-20"
    assert period.user_ids == [break_user.id]


@pytest.mark.integration
def test_create_break_period_open_ended(db, break_user):
    period = repository.create_break_period(
        None, "2026-03-10", None, "2026-03-01", [break_user.id]
    )

    assert period.label is None
    assert period.end_date is None


@pytest.mark.integration
def test_get_break_period_by_id_missing(db):
    assert repository.get_break_period_by_id(9999) is None


@pytest.mark.integration
def test_get_break_periods_orders_by_start_date_desc(db, break_user):
    repository.create_break_period("Later", "2026-04-01", None, "2026-03-01", [break_user.id])
    repository.create_break_period("Earlier", "2026-02-01", None, "2026-03-01", [break_user.id])

    periods = repository.get_break_periods()

    assert [p.label for p in periods] == ["Later", "Earlier"]


@pytest.mark.integration
def test_update_break_period(db, break_user):
    period = repository.create_break_period(
        "Old", "2026-03-10", None, "2026-03-01", [break_user.id]
    )

    repository.update_break_period(period.id, label="New", end_date="2026-03-25")

    updated = repository.get_break_period_by_id(period.id)
    assert updated.label == "New"
    assert updated.end_date == "2026-03-25"
    assert updated.start_date == "2026-03-10"


@pytest.mark.integration
def test_set_break_period_user_ids_replaces(db, break_user, break_user2):
    period = repository.create_break_period(
        "Test", "2026-03-10", None, "2026-03-01", [break_user.id]
    )

    repository.set_break_period_user_ids(period.id, [break_user.id, break_user2.id])

    updated = repository.get_break_period_by_id(period.id)
    assert set(updated.user_ids) == {break_user.id, break_user2.id}


@pytest.mark.integration
def test_delete_break_period(db, break_user):
    period = repository.create_break_period(
        "Test", "2026-03-10", None, "2026-03-01", [break_user.id]
    )

    assert repository.delete_break_period(period.id) is True
    assert repository.get_break_period_by_id(period.id) is None


@pytest.mark.integration
def test_delete_break_period_missing(db):
    assert repository.delete_break_period(9999) is False


@pytest.mark.integration
def test_get_active_break_period_user_ids(db, break_user, break_user2):
    repository.create_break_period("A", "2026-03-10", None, "2026-03-01", [break_user.id])
    repository.create_break_period(
        "B", "2026-04-01", "2026-04-10", "2026-03-01", [break_user2.id]
    )

    assert repository.get_active_break_period_user_ids("2026-03-15") == {break_user.id}
    assert repository.get_active_break_period_user_ids("2026-03-09") == set()
    expected = {break_user.id, break_user2.id}
    assert repository.get_active_break_period_user_ids("2026-04-05") == expected
    assert repository.get_active_break_period_user_ids("2026-04-11") == {break_user.id}


@pytest.mark.integration
def test_get_active_break_period_for_user(db, break_user):
    repository.create_break_period(
        "Vacaciones", "2026-03-10", "2026-03-20", "2026-03-01", [break_user.id]
    )

    active = repository.get_active_break_period_for_user(break_user.id, "2026-03-15")
    assert active is not None
    assert active.label == "Vacaciones"

    assert repository.get_active_break_period_for_user(break_user.id, "2026-03-21") is None
    assert repository.get_active_break_period_for_user(break_user.id, "2026-03-09") is None
    assert repository.get_active_break_period_for_user(9999, "2026-03-15") is None
