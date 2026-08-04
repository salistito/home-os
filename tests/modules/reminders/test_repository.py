import pytest

import modules.reminders.repository as repository
from modules.reminders.errors import ReminderAlreadyExistsError
from modules.reminders.types import ReminderOwner, ReminderRecurrence


@pytest.mark.integration
def test_create_reminder(db, db_user, frozen_today):
    reminder = repository.create_reminder(
        db_user.id, "msg", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
    )

    assert reminder.message == "Msg"
    assert reminder.trigger_at == "2026-04-01"
    assert reminder.trigger_time == "10:00"


@pytest.mark.integration
def test_get_reminder_by_id(db, db_user, frozen_today):
    reminder = repository.create_reminder(
        db_user.id, "msg", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
    )
    found = repository.get_reminder_by_id(reminder.id)

    assert found is not None
    assert found.id == reminder.id


@pytest.mark.integration
def test_get_reminder_by_message(db, db_user, frozen_today):
    repository.create_reminder(
        db_user.id, "msg", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
    )
    found = repository.get_reminder_by_message(db_user.id, "msg")

    assert found is not None
    assert found.message == "Msg"


@pytest.mark.integration
def test_get_reminders(db, db_user, frozen_today):
    repository.create_reminder(
        db_user.id, "msg", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
    )
    reminders = repository.get_reminders()

    assert len(reminders) >= 1


@pytest.mark.integration
def test_get_user_reminders(db, db_user, frozen_today):
    repository.create_reminder(
        db_user.id, "msg", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
    )
    reminders = repository.get_user_reminders(db_user.id)

    assert len(reminders) >= 1


@pytest.mark.integration
def test_get_user_pending_reminders(db, db_user, frozen_today):
    repository.create_reminder(
        db_user.id, "future", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
    )
    reminders = repository.get_user_pending_reminders(db_user.id, "2026-03-15")

    assert len(reminders) >= 1


@pytest.mark.integration
def test_get_due_day_reminders(db, db_user, frozen_today):
    repository.create_reminder(db_user.id, "due", "2026-03-15", None, ReminderRecurrence.NONE, None)
    reminders = repository.get_due_day_reminders("2026-04-02")

    assert len(reminders) >= 1


@pytest.mark.integration
def test_get_due_timed_reminders(db, db_user, frozen_today):
    repository.create_reminder(
        db_user.id, "timed", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
    )
    reminders = repository.get_due_timed_reminders("2026-04-01", "10:01")

    assert len(reminders) >= 1


@pytest.mark.integration
def test_update_reminder(db, db_user, frozen_today):
    reminder = repository.create_reminder(
        db_user.id, "msg", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
    )
    result = repository.update_reminder(reminder.id, db_user.id, message="new")

    assert result is True
    updated = repository.get_reminder_by_id(reminder.id)
    assert updated.message == "New"


@pytest.mark.integration
def test_delete_reminder(db, db_user, frozen_today):
    reminder = repository.create_reminder(
        db_user.id, "msg", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
    )
    result = repository.delete_reminder(reminder.id, db_user.id)

    assert result is True


@pytest.mark.integration
def test_update_reminder_cron_job_id(db, db_user, frozen_today):
    reminder = repository.create_reminder(
        db_user.id, "msg", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
    )
    repository.update_reminder_cron_job_id(reminder.id, "job123")
    updated = repository.get_reminder_by_id(reminder.id)

    assert updated.cron_job_id == "job123"


@pytest.mark.integration
def test_create_reminder_duplicate_message_raises(db, db_user, frozen_today):
    repository.create_reminder(
        db_user.id, "dupe", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
    )

    with pytest.raises(ReminderAlreadyExistsError):
        repository.create_reminder(
            db_user.id, "dupe", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
        )


@pytest.mark.integration
def test_update_reminder_no_fields_returns_true(db, db_user, frozen_today):
    reminder = repository.create_reminder(
        db_user.id, "msg", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
    )
    result = repository.update_reminder(reminder.id, db_user.id)

    assert result is True


@pytest.mark.integration
def test_update_reminder_invalid_columns_raises(db, db_user, frozen_today):
    reminder = repository.create_reminder(
        db_user.id, "msg", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
    )

    with pytest.raises(ValueError):
        repository.update_reminder(reminder.id, db_user.id, invalid_col="x")


@pytest.mark.integration
def test_update_reminder_sets_column_to_null(db, db_user, frozen_today):
    reminder = repository.create_reminder(
        db_user.id, "msg", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
    )
    result = repository.update_reminder(reminder.id, db_user.id, trigger_time=None)
    updated = repository.get_reminder_by_id(reminder.id)

    assert result is True
    assert updated.trigger_time is None


@pytest.mark.integration
def test_update_reminder_duplicate_message_raises(db, db_user, frozen_today):
    r1 = repository.create_reminder(
        db_user.id, "msg1", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
    )
    r2 = repository.create_reminder(
        db_user.id, "msg2", "2026-04-02", "10:00", ReminderRecurrence.NONE, None
    )

    with pytest.raises(ReminderAlreadyExistsError):
        repository.update_reminder(r2.id, db_user.id, message=r1.message)


@pytest.mark.integration
def test_upsert_system_reminder(db, db_user, frozen_today):
    reminder = repository.upsert_system_reminder(
        "food:low_stock", "5", db_user.id, "Low stock: milk", "2026-04-01"
    )

    assert reminder.owner == ReminderOwner.SYSTEM
    assert reminder.system_ref_entity == "food:low_stock"
    assert reminder.system_ref_entity_id == "5"
    assert reminder.message == "Low stock: milk"


@pytest.mark.integration
def test_upsert_system_reminder_replaces_existing(db, db_user, frozen_today):
    repository.upsert_system_reminder(
        "food:low_stock", "5", db_user.id, "Low stock: milk", "2026-04-01"
    )
    updated = repository.upsert_system_reminder(
        "food:low_stock", "5", db_user.id, "Low stock: milk (updated)", "2026-04-02"
    )

    assert updated.message == "Low stock: milk (updated)"
    assert updated.trigger_at == "2026-04-02"


@pytest.mark.integration
def test_get_system_reminder_by_entity(db, db_user, frozen_today):
    repository.upsert_system_reminder("food:low_stock", "5", db_user.id, "alert", "2026-04-01")
    found = repository.get_system_reminder_by_entity(db_user.id, "food:low_stock", "5")

    assert found is not None
    assert found.owner == ReminderOwner.SYSTEM


@pytest.mark.integration
def test_get_system_reminder_by_entity_not_found(db, db_user, frozen_today):
    found = repository.get_system_reminder_by_entity(db_user.id, "food:low_stock", "999")

    assert found is None


@pytest.mark.integration
def test_delete_system_reminders_by_entity(db, db_user, frozen_today):
    repository.upsert_system_reminder("food:low_stock", "5", db_user.id, "alert", "2026-04-01")
    repository.delete_system_reminders_by_entity(db_user.id, "food:low_stock", "5")
    found = repository.get_system_reminder_by_entity(db_user.id, "food:low_stock", "5")

    assert found is None


@pytest.mark.integration
def test_system_reminder_does_not_conflict_with_user_message(db, db_user, frozen_today):
    repository.create_reminder(
        db_user.id, "alert", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
    )
    system_reminder = repository.upsert_system_reminder(
        "food:low_stock", "5", db_user.id, "alert", "2026-04-01"
    )

    assert system_reminder.owner == ReminderOwner.SYSTEM
    user_reminder = repository.get_reminder_by_message(db_user.id, "alert")
    assert user_reminder.owner == ReminderOwner.USER


@pytest.mark.integration
def test_get_user_reminders_excludes_system(db, db_user, frozen_today):
    repository.create_reminder(
        db_user.id, "user msg", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
    )
    repository.upsert_system_reminder("food:low_stock", "5", db_user.id, "system msg", "2026-04-01")
    reminders = repository.get_user_reminders(db_user.id)

    assert len(reminders) == 1
    assert reminders[0].owner == ReminderOwner.USER


@pytest.mark.integration
def test_get_user_pending_reminders_excludes_system(db, db_user, frozen_today):
    repository.create_reminder(
        db_user.id, "user future", "2026-04-01", "10:00", ReminderRecurrence.NONE, None
    )
    repository.upsert_system_reminder("food:low_stock", "5", db_user.id, "system msg", "2026-04-01")
    reminders = repository.get_user_pending_reminders(db_user.id, "2026-03-15")

    assert len(reminders) == 1
    assert reminders[0].owner == ReminderOwner.USER


@pytest.mark.integration
def test_get_due_reminders_include_system(db, db_user, frozen_today):
    repository.upsert_system_reminder("food:low_stock", "5", db_user.id, "system due", "2026-04-01")
    reminders = repository.get_due_day_reminders("2026-04-02")

    system_reminders = [r for r in reminders if r.owner == ReminderOwner.SYSTEM]
    assert len(system_reminders) == 1


@pytest.mark.integration
def test_get_reminder_by_message_excludes_system(db, db_user, frozen_today):
    repository.upsert_system_reminder("food:low_stock", "5", db_user.id, "shared msg", "2026-04-01")
    found = repository.get_reminder_by_message(db_user.id, "shared msg")

    assert found is None


@pytest.mark.integration
def test_update_reminder_rejects_system_reminder(db, db_user, frozen_today):
    system_reminder = repository.upsert_system_reminder(
        "food:low_stock", "5", db_user.id, "system msg", "2026-04-01"
    )
    result = repository.update_reminder(system_reminder.id, db_user.id, message="hacked")

    assert result is False
    unchanged = repository.get_reminder_by_id(system_reminder.id)
    assert unchanged.message == "system msg"


@pytest.mark.integration
def test_delete_reminder_rejects_system_reminder(db, db_user, frozen_today):
    system_reminder = repository.upsert_system_reminder(
        "food:low_stock", "5", db_user.id, "system msg", "2026-04-01"
    )
    result = repository.delete_reminder(system_reminder.id, db_user.id)

    assert result is False
    assert repository.get_reminder_by_id(system_reminder.id) is not None


@pytest.mark.integration
def test_delete_system_reminder_works_for_any_owner(db, db_user, frozen_today):
    system_reminder = repository.upsert_system_reminder(
        "food:low_stock", "5", db_user.id, "system msg", "2026-04-01"
    )
    result = repository.delete_system_reminder(system_reminder.id)

    assert result is True
    assert repository.get_reminder_by_id(system_reminder.id) is None


@pytest.mark.integration
def test_upsert_system_reminder_with_trigger_time(db, db_user, frozen_today):
    reminder = repository.upsert_system_reminder(
        "food:low_stock",
        "5",
        db_user.id,
        "Stock alert",
        "2026-04-01",
        trigger_time="10:00",
    )

    assert reminder.trigger_time == "10:00"
    assert reminder.recurrence == ReminderRecurrence.NONE


@pytest.mark.integration
def test_upsert_system_reminder_with_recurrence(db, db_user, frozen_today):
    reminder = repository.upsert_system_reminder(
        "food:low_stock",
        "5",
        db_user.id,
        "Daily check",
        "2026-04-01",
        recurrence=ReminderRecurrence.DAILY,
    )

    assert reminder.recurrence == ReminderRecurrence.DAILY


@pytest.mark.integration
def test_upsert_system_reminder_with_cron_job_id(db, db_user, frozen_today):
    reminder = repository.upsert_system_reminder(
        "food:low_stock",
        "5",
        db_user.id,
        "Timed alert",
        "2026-04-01",
        trigger_time="14:30",
        cron_job_id="job123",
    )

    assert reminder.trigger_time == "14:30"
    assert reminder.cron_job_id == "job123"


@pytest.mark.integration
def test_update_reminder_trigger_at(db, db_user, frozen_today):
    reminder = repository.upsert_system_reminder(
        "food:low_stock", "5", db_user.id, "alert", "2026-04-01"
    )
    repository.update_reminder_trigger_at(reminder.id, "2026-05-01")
    updated = repository.get_reminder_by_id(reminder.id)

    assert updated.trigger_at == "2026-05-01"


@pytest.mark.integration
def test_create_reminder_custom_recurrence_roundtrip(db, db_user, frozen_today):
    reminder = repository.create_reminder(
        db_user.id, "msg", "2026-04-01", "14:00", "2d", None
    )

    assert reminder.recurrence == "2d"
    found = repository.get_reminder_by_id(reminder.id)
    assert found.recurrence == "2d"


@pytest.mark.integration
def test_update_reminder_schedule(db, db_user, frozen_today):
    reminder = repository.create_reminder(
        db_user.id, "msg", "2026-04-01", "14:00", "12h", None
    )
    repository.update_reminder_schedule(reminder.id, "2026-04-02", "02:00")
    updated = repository.get_reminder_by_id(reminder.id)

    assert updated.trigger_at == "2026-04-02"
    assert updated.trigger_time == "02:00"
