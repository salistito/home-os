import pytest

from datetime import datetime
from unittest.mock import patch

from modules.reminders.errors import ReminderAlreadyExistsError
from modules.reminders.service import (
    calculate_next_trigger_at,
    advance_recurrence,
    create_reminder,
    delete_reminder,
    delete_reminder_by_message,
    get_due_day_reminders,
    get_due_timed_reminders,
    get_user_pending_reminders,
    get_user_reminders,
    is_past,
    process_reminder_states,
    update_reminder,
)
from modules.reminders.types import (
    Reminder,
    ReminderOperationStatus,
    ReminderRecurrence,
)


@pytest.fixture
def mock_reminder():
    return Reminder(
        1,
        1,
        "Test message",
        "2026-04-01",
        "10:00",
        ReminderRecurrence.DAILY,
        "job123",
        "2026-03-15",
    )


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_create_reminder_valid(mock_repo, mock_cron, mock_now, mock_reminder):
    mock_now.return_value = datetime(2026, 3, 15, 10, 30)
    mock_cron.create_one_shot_job.return_value = "job123"
    mock_repo.create_reminder.return_value = mock_reminder

    result = create_reminder(1, "Test message", "2026-04-01", "10:00", "daily")

    assert result.status == ReminderOperationStatus.OK
    assert result.reminder == mock_reminder


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
@patch("modules.reminders.service.repository")
def test_create_reminder_empty_message(mock_repo, mock_now):
    mock_now.return_value = datetime(2026, 3, 15, 10, 30)

    result = create_reminder(1, "", "2026-04-01", "10:00", "daily")

    assert result.status == ReminderOperationStatus.INVALID


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
@patch("modules.reminders.service.repository")
def test_create_reminder_invalid_recurrence(mock_repo, mock_now):
    mock_now.return_value = datetime(2026, 3, 15, 10, 30)

    result = create_reminder(1, "msg", "2026-04-01", "10:00", "invalid")

    assert result.status == ReminderOperationStatus.INVALID


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
@patch("modules.reminders.service.repository")
def test_create_reminder_invalid_date(mock_repo, mock_now):
    mock_now.return_value = datetime(2026, 3, 15, 10, 30)

    result = create_reminder(1, "msg", "not-a-date", "10:00", "daily")

    assert result.status == ReminderOperationStatus.INVALID


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
@patch("modules.reminders.service.repository")
def test_create_reminder_invalid_time(mock_repo, mock_now):
    mock_now.return_value = datetime(2026, 3, 15, 10, 30)

    result = create_reminder(1, "msg", "2026-04-01", "25:00", "daily")

    assert result.status == ReminderOperationStatus.INVALID


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
@patch("modules.reminders.service.repository")
def test_create_reminder_past_time(mock_repo, mock_now):
    mock_now.return_value = datetime(2026, 3, 15, 10, 30)

    result = create_reminder(1, "msg", "2026-01-01", "10:00", "daily")

    assert result.status == ReminderOperationStatus.PAST_TIME


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_create_reminder_duplicate_cleans_up_cron(mock_repo, mock_cron, mock_now, mock_reminder):
    mock_now.return_value = datetime(2026, 3, 15, 10, 30)
    mock_cron.create_one_shot_job.return_value = "job123"
    mock_repo.create_reminder.side_effect = ReminderAlreadyExistsError(mock_reminder)

    result = create_reminder(1, "Test message", "2026-04-01", "10:00", "daily")

    assert result.status == ReminderOperationStatus.DUPLICATE_MESSAGE
    mock_cron.delete_job.assert_called_once_with("job123")


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_create_reminder_with_trigger_time_creates_cron_job(
    mock_repo, mock_cron, mock_now, mock_reminder
):
    mock_now.return_value = datetime(2026, 3, 15, 10, 30)
    mock_cron.create_one_shot_job.return_value = "job456"
    mock_repo.create_reminder.return_value = mock_reminder

    result = create_reminder(1, "Test message", "2026-04-01", "10:00", "daily")

    mock_cron.create_one_shot_job.assert_called_once_with("2026-04-01", "10:00")
    assert result.status == ReminderOperationStatus.OK


@pytest.mark.unit
@patch("modules.reminders.service.repository")
def test_update_reminder_not_found(mock_repo):
    mock_repo.get_reminder_by_id.return_value = None
    result = update_reminder(1, 1, message="new")

    assert result.status == ReminderOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.reminders.service.repository")
def test_update_reminder_wrong_owner(mock_repo, mock_reminder):
    mock_repo.get_reminder_by_id.return_value = mock_reminder
    result = update_reminder(1, 999, message="new")

    assert result.status == ReminderOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_update_reminder_valid(mock_repo, mock_cron, mock_now, mock_reminder):
    mock_now.return_value = datetime(2026, 3, 15, 10, 30)
    mock_repo.EDITABLE_REMINDER_COLUMNS = {
        "message",
        "trigger_at",
        "trigger_time",
        "recurrence",
        "cron_job_id",
    }
    mock_reminder.cron_job_id = None
    mock_repo.get_reminder_by_id.side_effect = [mock_reminder, mock_reminder]

    result = update_reminder(1, 1, message="new")

    assert result.status == ReminderOperationStatus.OK


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_update_reminder_time_changed_updates_cron(mock_repo, mock_cron, mock_now, mock_reminder):
    mock_now.return_value = datetime(2026, 3, 15, 10, 30)
    mock_repo.EDITABLE_REMINDER_COLUMNS = {
        "message",
        "trigger_at",
        "trigger_time",
        "recurrence",
        "cron_job_id",
    }
    updated = Reminder(
        1,
        1,
        "Test message",
        "2026-05-01",
        "12:00",
        ReminderRecurrence.DAILY,
        "job123",
        "2026-03-15",
    )
    mock_repo.get_reminder_by_id.side_effect = [mock_reminder, updated]
    result = update_reminder(1, 1, trigger_at="2026-05-01")

    assert result.status == ReminderOperationStatus.OK
    mock_cron.update_job.assert_called_once_with("job123", "2026-05-01", "12:00")


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_update_reminder_time_changed_creates_cron(mock_repo, mock_cron, mock_now):
    mock_now.return_value = datetime(2026, 3, 15, 10, 30)
    mock_repo.EDITABLE_REMINDER_COLUMNS = {
        "message",
        "trigger_at",
        "trigger_time",
        "recurrence",
        "cron_job_id",
    }
    reminder = Reminder(
        1,
        1,
        "Test message",
        "2026-04-01",
        "10:00",
        ReminderRecurrence.DAILY,
        None,
        "2026-03-15",
    )
    updated = Reminder(
        1,
        1,
        "Test message",
        "2026-05-01",
        "12:00",
        ReminderRecurrence.DAILY,
        None,
        "2026-03-15",
    )
    mock_cron.create_one_shot_job.return_value = "newjob"
    mock_repo.get_reminder_by_id.side_effect = [reminder, updated, updated]
    result = update_reminder(1, 1, trigger_at="2026-05-01", trigger_time="12:00")

    assert result.status == ReminderOperationStatus.OK
    mock_cron.create_one_shot_job.assert_called_once_with("2026-05-01", "12:00")


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_update_reminder_time_changed_deletes_cron(mock_repo, mock_cron, mock_now):
    mock_now.return_value = datetime(2026, 3, 15, 10, 30)
    mock_repo.EDITABLE_REMINDER_COLUMNS = {
        "message",
        "trigger_at",
        "trigger_time",
        "recurrence",
        "cron_job_id",
    }
    reminder = Reminder(
        1,
        1,
        "Test message",
        "2026-04-01",
        "10:00",
        ReminderRecurrence.DAILY,
        "job123",
        "2026-03-15",
    )
    updated = Reminder(
        1,
        1,
        "Test message",
        "2026-04-01",
        None,
        ReminderRecurrence.DAILY,
        "job123",
        "2026-03-15",
    )
    mock_repo.get_reminder_by_id.side_effect = [reminder, updated, updated]
    result = update_reminder(1, 1, trigger_time=None)

    assert result.status == ReminderOperationStatus.OK
    mock_cron.delete_job.assert_called_once_with("job123")


@pytest.mark.unit
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_delete_reminder_not_found(mock_repo, mock_cron):
    mock_repo.get_reminder_by_id.return_value = None
    result = delete_reminder(1, 1)

    assert result.status == ReminderOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_delete_reminder_with_cron_job(mock_repo, mock_cron, mock_reminder):
    mock_repo.get_reminder_by_id.return_value = mock_reminder
    mock_repo.delete_reminder.return_value = True
    result = delete_reminder(1, 1)

    assert result.status == ReminderOperationStatus.OK
    mock_cron.delete_job.assert_called_once_with("job123")


@pytest.mark.unit
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_delete_reminder_success(mock_repo, mock_cron, mock_reminder):
    mock_reminder.cron_job_id = None
    mock_repo.get_reminder_by_id.return_value = mock_reminder
    mock_repo.delete_reminder.return_value = True
    result = delete_reminder(1, 1)

    assert result.status == ReminderOperationStatus.OK


@pytest.mark.unit
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_delete_reminder_by_message_not_found(mock_repo, mock_cron):
    mock_repo.get_reminder_by_message.return_value = None
    result = delete_reminder_by_message(1, "msg")

    assert result.status == ReminderOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_delete_reminder_by_message_with_cron(mock_repo, mock_cron, mock_reminder):
    mock_repo.get_reminder_by_message.return_value = mock_reminder
    mock_repo.delete_reminder.return_value = True
    result = delete_reminder_by_message(1, "msg")

    assert result.status == ReminderOperationStatus.OK
    mock_cron.delete_job.assert_called_once_with("job123")


@pytest.mark.unit
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_advance_recurrence_daily(mock_repo, mock_cron, mock_reminder):
    mock_reminder.cron_job_id = None
    mock_reminder.trigger_time = None
    mock_repo.get_reminder_by_id.return_value = mock_reminder

    advance_recurrence(mock_reminder)

    mock_repo.update_reminder.assert_called_once()


@pytest.mark.unit
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_advance_recurrence_weekly(mock_repo, mock_cron, mock_reminder):
    mock_reminder.recurrence = ReminderRecurrence.WEEKLY
    mock_reminder.cron_job_id = None
    mock_reminder.trigger_time = None
    mock_repo.get_reminder_by_id.return_value = mock_reminder

    advance_recurrence(mock_reminder)

    mock_repo.update_reminder.assert_called_once()


@pytest.mark.unit
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_advance_recurrence_monthly(mock_repo, mock_cron, mock_reminder):
    mock_reminder.recurrence = ReminderRecurrence.MONTHLY
    mock_reminder.cron_job_id = None
    mock_reminder.trigger_time = None
    mock_repo.get_reminder_by_id.return_value = mock_reminder

    advance_recurrence(mock_reminder)

    mock_repo.update_reminder.assert_called_once()


@pytest.mark.unit
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_advance_recurrence_yearly(mock_repo, mock_cron, mock_reminder):
    mock_reminder.recurrence = ReminderRecurrence.YEARLY
    mock_reminder.cron_job_id = None
    mock_reminder.trigger_time = None
    mock_repo.get_reminder_by_id.return_value = mock_reminder

    advance_recurrence(mock_reminder)

    mock_repo.update_reminder.assert_called_once()


@pytest.mark.unit
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_advance_recurrence_none_returns_none(mock_repo, mock_cron, mock_reminder):
    mock_reminder.recurrence = ReminderRecurrence.NONE
    result = advance_recurrence(mock_reminder)

    assert result is None


@pytest.mark.unit
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_advance_recurrence_with_cron_updates(mock_repo, mock_cron, mock_reminder):
    mock_reminder.trigger_time = "10:00"
    mock_reminder.cron_job_id = "job123"
    mock_repo.get_reminder_by_id.return_value = mock_reminder

    advance_recurrence(mock_reminder)

    mock_cron.update_job.assert_called_once()


@pytest.mark.unit
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_advance_recurrence_with_time_no_cron_creates(mock_repo, mock_cron, mock_reminder):
    mock_reminder.trigger_time = "10:00"
    mock_reminder.cron_job_id = None
    mock_cron.create_one_shot_job.return_value = "newjob"
    mock_repo.get_reminder_by_id.return_value = mock_reminder

    advance_recurrence(mock_reminder)

    mock_cron.create_one_shot_job.assert_called_once()


@pytest.mark.unit
@patch("modules.reminders.service.delete_reminder")
def test_process_reminder_states_none_deletes(mock_delete, mock_reminder):
    mock_reminder.recurrence = ReminderRecurrence.NONE
    process_reminder_states([mock_reminder])

    mock_delete.assert_called_once_with(mock_reminder.id, mock_reminder.user_id)


@pytest.mark.unit
@patch("modules.reminders.service.advance_recurrence")
def test_process_reminder_states_recurring_advances(mock_advance, mock_reminder):
    mock_reminder.recurrence = ReminderRecurrence.DAILY
    process_reminder_states([mock_reminder])

    mock_advance.assert_called_once_with(mock_reminder)


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
def test_is_past_past_date(mock_get_now):
    mock_get_now.return_value = datetime(2026, 3, 15, 10, 30)
    result = is_past("2026-01-01", "10:00")

    assert result is True


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
def test_is_past_future_date(mock_get_now):
    mock_get_now.return_value = datetime(2026, 3, 15, 10, 30)
    result = is_past("2026-12-01", "10:00")

    assert result is False


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
def test_is_past_same_date_no_time(mock_get_now):
    mock_get_now.return_value = datetime(2026, 3, 15, 10, 30)
    result = is_past("2026-03-15", None)

    assert result is True


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
def test_is_past_same_date_past_time(mock_get_now):
    mock_get_now.return_value = datetime(2026, 3, 15, 10, 30)
    result = is_past("2026-03-15", "09:00")

    assert result is True


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
def test_is_past_same_date_future_time(mock_get_now):
    mock_get_now.return_value = datetime(2026, 3, 15, 12, 30)
    result = is_past("2026-03-15", "13:00")

    assert result is False


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
@patch("modules.reminders.service.repository")
def test_get_user_reminders_delegates(mock_repo, mock_get_now):
    mock_repo.get_user_reminders.return_value = []
    result = get_user_reminders(1)

    assert result == []
    mock_repo.get_user_reminders.assert_called_once_with(1)


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
@patch("modules.reminders.service.repository")
def test_get_user_pending_reminders_delegates(mock_repo, mock_get_now):
    mock_get_now.return_value = datetime(2026, 3, 15, 10, 30)
    mock_repo.get_user_pending_reminders.return_value = []
    result = get_user_pending_reminders(1)

    assert result == []
    mock_repo.get_user_pending_reminders.assert_called_once_with(1, "2026-03-15")


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
@patch("modules.reminders.service.repository")
def test_get_due_day_reminders_delegates(mock_repo, mock_get_now):
    mock_get_now.return_value = datetime(2026, 3, 15, 10, 30)
    mock_repo.get_due_day_reminders.return_value = []
    result = get_due_day_reminders()

    assert result == []
    mock_repo.get_due_day_reminders.assert_called_once_with("2026-03-15")


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
@patch("modules.reminders.service.repository")
def test_get_due_timed_reminders_delegates(mock_repo, mock_get_now):
    mock_get_now.return_value = datetime(2026, 3, 15, 10, 30)
    mock_repo.get_due_timed_reminders.return_value = []
    result = get_due_timed_reminders()

    assert result == []
    mock_repo.get_due_timed_reminders.assert_called_once_with("2026-03-15", "10:30")


@pytest.mark.unit
def test_calculate_next_trigger_at_monthly_december_wrap():
    result = calculate_next_trigger_at("2026-12-15", "monthly")

    assert result == "2027-01-15T00:00:00"


@pytest.mark.unit
def test_calculate_next_trigger_at_yearly():
    result = calculate_next_trigger_at("2026-03-15", "yearly")

    assert result == "2027-03-15T00:00:00"


@pytest.mark.unit
def test_calculate_next_trigger_at_invalid_returns_none():
    result = calculate_next_trigger_at("2026-03-15", "invalid")

    assert result is None


@pytest.mark.unit
def test_calculate_next_trigger_at_none_returns_none():
    result = calculate_next_trigger_at("2026-03-15", "none")

    assert result is None


@pytest.mark.unit
def test_calculate_next_trigger_at_weekly():
    result = calculate_next_trigger_at("2026-03-15", "weekly")

    assert result == "2026-03-22T00:00:00"


@pytest.mark.unit
def test_calculate_next_trigger_at_daily():
    result = calculate_next_trigger_at("2026-03-15", "daily")

    assert result == "2026-03-16T00:00:00"


@pytest.mark.unit
@patch("modules.reminders.service.repository")
def test_update_reminder_no_valid_fields_invalid(mock_repo, mock_reminder):
    mock_repo.EDITABLE_REMINDER_COLUMNS = {
        "message",
        "trigger_at",
        "trigger_time",
        "recurrence",
        "cron_job_id",
    }
    mock_repo.get_reminder_by_id.return_value = mock_reminder
    result = update_reminder(1, 1)

    assert result.status == ReminderOperationStatus.INVALID


@pytest.mark.unit
@patch("modules.reminders.service.repository")
def test_update_reminder_empty_message_invalid(mock_repo, mock_reminder):
    mock_repo.EDITABLE_REMINDER_COLUMNS = {
        "message",
        "trigger_at",
        "trigger_time",
        "recurrence",
        "cron_job_id",
    }
    mock_repo.get_reminder_by_id.return_value = mock_reminder
    result = update_reminder(1, 1, message="")

    assert result.status == ReminderOperationStatus.INVALID


@pytest.mark.unit
@patch("modules.reminders.service.repository")
def test_update_reminder_invalid_trigger_at(mock_repo, mock_reminder):
    mock_repo.EDITABLE_REMINDER_COLUMNS = {
        "message",
        "trigger_at",
        "trigger_time",
        "recurrence",
        "cron_job_id",
    }
    mock_repo.get_reminder_by_id.return_value = mock_reminder
    result = update_reminder(1, 1, trigger_at="2026-13-01")

    assert result.status == ReminderOperationStatus.INVALID


@pytest.mark.unit
@patch("modules.reminders.service.repository")
def test_update_reminder_invalid_trigger_time(mock_repo, mock_reminder):
    mock_repo.EDITABLE_REMINDER_COLUMNS = {
        "message",
        "trigger_at",
        "trigger_time",
        "recurrence",
        "cron_job_id",
    }
    mock_repo.get_reminder_by_id.return_value = mock_reminder
    result = update_reminder(1, 1, trigger_time="25:00")

    assert result.status == ReminderOperationStatus.INVALID


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
@patch("modules.reminders.service.repository")
def test_update_reminder_past_time(mock_repo, mock_now, mock_reminder):
    mock_now.return_value = datetime(2026, 3, 15, 10, 30)
    mock_repo.EDITABLE_REMINDER_COLUMNS = {
        "message",
        "trigger_at",
        "trigger_time",
        "recurrence",
        "cron_job_id",
    }
    mock_reminder.trigger_at = "2026-04-01"
    mock_reminder.trigger_time = "10:00"
    mock_repo.get_reminder_by_id.return_value = mock_reminder
    result = update_reminder(1, 1, trigger_at="2020-01-01")

    assert result.status == ReminderOperationStatus.PAST_TIME


@pytest.mark.unit
@patch("modules.reminders.service.get_now")
@patch("modules.reminders.service.repository")
def test_update_reminder_invalid_recurrence(mock_repo, mock_now, mock_reminder):
    mock_now.return_value = datetime(2025, 1, 1, 10, 30)
    mock_repo.EDITABLE_REMINDER_COLUMNS = {
        "message",
        "trigger_at",
        "trigger_time",
        "recurrence",
        "cron_job_id",
    }
    mock_repo.get_reminder_by_id.return_value = mock_reminder
    result = update_reminder(1, 1, recurrence="invalid")

    assert result.status == ReminderOperationStatus.INVALID


@pytest.mark.unit
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_delete_reminder_not_found_when_repository_delete_returns_false(
    mock_repo, mock_cron, mock_reminder
):
    mock_repo.get_reminder_by_id.return_value = mock_reminder
    mock_repo.delete_reminder.return_value = False
    result = delete_reminder(1, 1)

    assert result.status == ReminderOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.reminders.service.cron")
@patch("modules.reminders.service.repository")
def test_delete_reminder_by_message_not_found_when_repo_delete_false(
    mock_repo, mock_cron, mock_reminder
):
    mock_repo.get_reminder_by_message.return_value = mock_reminder
    mock_repo.delete_reminder.return_value = False
    result = delete_reminder_by_message(1, "msg")

    assert result.status == ReminderOperationStatus.NOT_FOUND
