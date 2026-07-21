import pytest

import modules.finances.repository as repository
from modules.finances.errors import OpenPeriodExistsError


@pytest.mark.integration
def test_create_period(db, frozen_today):
    period = repository.create_period("Test Period", "2026-03-15")

    assert period.label == "Test Period"
    assert period.status == "open"


@pytest.mark.integration
def test_create_period_second_raises(db, frozen_today):
    repository.create_period("Period A", "2026-03-15")

    with pytest.raises(OpenPeriodExistsError):
        repository.create_period("Period B", "2026-03-16")


@pytest.mark.integration
def test_close_open_period(db, frozen_today):
    repository.create_period("Test Period", "2026-03-15")
    repository.close_open_period()
    period = repository.get_open_period()

    assert period is None


@pytest.mark.integration
def test_get_open_period(db, frozen_today):
    repository.create_period("Test Period", "2026-03-15")
    period = repository.get_open_period()

    assert period is not None
    assert period.status == "open"


@pytest.mark.integration
def test_get_period_by_id(db, frozen_today):
    created = repository.create_period("Test Period", "2026-03-15")
    found = repository.get_period_by_id(created.id)

    assert found is not None
    assert found.id == created.id


@pytest.mark.integration
def test_get_period_by_label(db, frozen_today):
    repository.create_period("Test Period", "2026-03-15")
    found = repository.get_period_by_label("Test Period")

    assert found is not None


@pytest.mark.integration
def test_get_periods(db, frozen_today):
    repository.create_period("Test Period", "2026-03-15")
    periods = repository.get_periods()

    assert len(periods) >= 1


@pytest.mark.integration
def test_create_entry(db, db_user, frozen_today):
    period = repository.create_period("Test Period", "2026-03-15")
    entry = repository.create_entry(
        period.id, "income", "personal", db_user.id, "Salary", 5000, "2026-03-15"
    )

    assert entry is not None
    assert entry.label == "Salary"
    assert entry.amount == 5000
    assert entry.status == "confirmed"


@pytest.mark.integration
def test_create_entry_pending_when_no_amount(db, db_user, frozen_today):
    period = repository.create_period("Test Period", "2026-03-15")
    entry = repository.create_entry(
        period.id, "expense", "shared", db_user.id, "Rent", None, "2026-03-15"
    )

    assert entry is not None
    assert entry.amount is None
    assert entry.status == "pending"


@pytest.mark.integration
def test_update_entry(db, db_user, frozen_today):
    period = repository.create_period("Test Period", "2026-03-15")
    entry = repository.create_entry(
        period.id, "income", "personal", db_user.id, "Salary", 5000, "2026-03-15"
    )
    updated = repository.update_entry(entry.id, "Bonus", db_user.id, 3000, "none")

    assert updated is not None
    assert updated.label == "Bonus"
    assert updated.amount == 3000


@pytest.mark.integration
def test_replace_entry_details(db, db_user, frozen_today):
    period = repository.create_period("Test Period", "2026-03-15")
    entry = repository.create_entry(
        period.id, "expense", "shared", db_user.id, "Shop", 300, "2026-03-15"
    )
    repository.replace_entry_details(entry.id, [("Part A", 100), ("Part B", 200)])


@pytest.mark.integration
def test_clone_confirmed_entries(db, db_user, frozen_today):
    period1 = repository.create_period("Period A", "2026-03-15")
    repository.create_entry(
        period1.id, "income", "personal", db_user.id, "Salary", 5000, "2026-03-15"
    )

    repository.close_open_period()
    period2 = repository.create_period("Period B", "2026-04-15")
    repository.clone_confirmed_entries(period1.id, period2.id, "2026-04-15")

    entries = repository.get_entries_by_period(period2.id)
    assert len(entries) == 1
    assert entries[0].status == "pending"


@pytest.mark.integration
def test_set_entry_status(db, db_user, frozen_today):
    period = repository.create_period("Test Period", "2026-03-15")
    entry = repository.create_entry(
        period.id, "income", "personal", db_user.id, "Salary", 5000, "2026-03-15"
    )
    updated = repository.set_entry_status(entry.id, "confirmed", "2026-03-16")

    assert updated is not None
    assert updated.status == "confirmed"
    assert updated.paid_at == "2026-03-16"


@pytest.mark.integration
def test_delete_entry(db, db_user, frozen_today):
    period = repository.create_period("Test Period", "2026-03-15")
    entry = repository.create_entry(
        period.id, "income", "personal", db_user.id, "Salary", 5000, "2026-03-15"
    )
    repository.delete_entry(entry.id)
    found = repository.get_entry_by_id(entry.id)

    assert found is None


@pytest.mark.integration
def test_get_entry_by_id_with_details(db, db_user, frozen_today):
    period = repository.create_period("Test Period", "2026-03-15")
    entry = repository.create_entry(
        period.id, "income", "personal", db_user.id, "Salary", 5000, "2026-03-15"
    )
    repository.replace_entry_details(entry.id, [("Base", 4000), ("Bonus", 1000)])

    found = repository.get_entry_by_id(entry.id)
    assert len(found.details) == 2


@pytest.mark.integration
def test_get_entries_by_period(db, db_user, frozen_today):
    period = repository.create_period("Test Period", "2026-03-15")
    repository.create_entry(
        period.id, "income", "personal", db_user.id, "Salary", 5000, "2026-03-15"
    )
    entries = repository.get_entries_by_period(period.id)

    assert len(entries) >= 1


@pytest.mark.integration
def test_get_tags(db):
    tags = repository.get_tags()

    assert isinstance(tags, list)


@pytest.mark.integration
def test_get_or_create_tag_ids_new(db, frozen_today):
    ids = repository.get_or_create_tag_ids(["groceries"], "2026-03-15")

    assert len(ids) == 1


@pytest.mark.integration
def test_get_or_create_tag_ids_existing(db, frozen_today):
    ids1 = repository.get_or_create_tag_ids(["existing"], "2026-03-15")
    ids2 = repository.get_or_create_tag_ids(["existing"], "2026-03-15")

    assert len(ids2) == 1
    assert ids2[0] == ids1[0]


@pytest.mark.integration
def test_set_entry_tags(db, db_user, frozen_today):
    period = repository.create_period("Test Period", "2026-03-15")
    entry = repository.create_entry(
        period.id, "income", "personal", db_user.id, "Salary", 5000, "2026-03-15"
    )
    tag_ids = repository.get_or_create_tag_ids(["work"], "2026-03-15")
    repository.set_entry_tags(entry.id, tag_ids)

    found = repository.get_entry_by_id(entry.id)
    assert len(found.tags) >= 1


@pytest.mark.integration
def test_set_entry_tags_empty_clears(db, db_user, frozen_today):
    period = repository.create_period("Test Period", "2026-03-15")
    entry = repository.create_entry(
        period.id, "income", "personal", db_user.id, "Salary", 5000, "2026-03-15"
    )
    repository.set_entry_tags(entry.id, [])

    found = repository.get_entry_by_id(entry.id)
    assert len(found.tags) == 0


@pytest.mark.integration
def test_get_entries_by_period_empty_list(db, frozen_today):
    period = repository.create_period("Test Period", "2026-03-15")
    entries = repository.get_entries_by_period(period.id)

    assert entries == []
