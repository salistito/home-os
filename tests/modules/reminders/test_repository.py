import pytest

import modules.reminders.repository as repository
from modules.reminders.errors import ReminderAlreadyExistsError
from modules.reminders.types import ReminderRecurrence


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
