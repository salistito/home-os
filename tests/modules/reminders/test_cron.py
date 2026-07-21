import pytest

from unittest.mock import MagicMock, patch


@pytest.mark.unit
def test_create_one_shot_job_success(monkeypatch):
    monkeypatch.setattr("modules.reminders.cron.CRONJOB_ORG_API_KEY", "test-key")
    monkeypatch.setattr("modules.reminders.cron.WEBHOOK_URL", "https://example.com/webhook")
    monkeypatch.setattr("modules.reminders.cron.WEBHOOK_SECRET", "secret")

    mock_response = MagicMock()
    mock_response.json.return_value = {"jobId": 42}
    mock_response.raise_for_status = MagicMock()

    with patch("modules.reminders.cron.httpx.put", return_value=mock_response) as mock_put:
        from modules.reminders.cron import create_one_shot_job

        result = create_one_shot_job("2026-04-01", "10:00")

        assert result == "42"
        mock_put.assert_called_once()


@pytest.mark.unit
def test_create_one_shot_job_not_configured(monkeypatch):
    monkeypatch.setattr("modules.reminders.cron.CRONJOB_ORG_API_KEY", "")
    monkeypatch.setattr("modules.reminders.cron.WEBHOOK_URL", "")
    monkeypatch.setattr("modules.reminders.cron.WEBHOOK_SECRET", "")

    from modules.reminders.cron import create_one_shot_job

    result = create_one_shot_job("2026-04-01", "10:00")

    assert result is None


@pytest.mark.unit
def test_create_one_shot_job_api_failure(monkeypatch):
    monkeypatch.setattr("modules.reminders.cron.CRONJOB_ORG_API_KEY", "test-key")
    monkeypatch.setattr("modules.reminders.cron.WEBHOOK_URL", "https://example.com/webhook")
    monkeypatch.setattr("modules.reminders.cron.WEBHOOK_SECRET", "secret")

    with patch("modules.reminders.cron.httpx.put", side_effect=Exception("fail")):
        from modules.reminders.cron import create_one_shot_job

        result = create_one_shot_job("2026-04-01", "10:00")

        assert result is None


@pytest.mark.unit
def test_update_job_success(monkeypatch):
    monkeypatch.setattr("modules.reminders.cron.CRONJOB_ORG_API_KEY", "test-key")

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("modules.reminders.cron.httpx.patch", return_value=mock_response) as mock_patch:
        from modules.reminders.cron import update_job

        result = update_job("job123", "2026-04-01", "10:00")

        assert result is True
        mock_patch.assert_called_once()


@pytest.mark.unit
def test_update_job_not_configured(monkeypatch):
    monkeypatch.setattr("modules.reminders.cron.CRONJOB_ORG_API_KEY", "")

    from modules.reminders.cron import update_job

    result = update_job("job123", "2026-04-01", "10:00")

    assert result is False


@pytest.mark.unit
def test_update_job_api_failure(monkeypatch):
    monkeypatch.setattr("modules.reminders.cron.CRONJOB_ORG_API_KEY", "test-key")

    with patch("modules.reminders.cron.httpx.patch", side_effect=Exception("fail")):
        from modules.reminders.cron import update_job

        result = update_job("job123", "2026-04-01", "10:00")

        assert result is False


@pytest.mark.unit
def test_delete_job_success(monkeypatch):
    monkeypatch.setattr("modules.reminders.cron.CRONJOB_ORG_API_KEY", "test-key")

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("modules.reminders.cron.httpx.delete", return_value=mock_response) as mock_delete:
        from modules.reminders.cron import delete_job

        result = delete_job("job123")

        assert result is True
        mock_delete.assert_called_once()


@pytest.mark.unit
def test_delete_job_not_configured(monkeypatch):
    monkeypatch.setattr("modules.reminders.cron.CRONJOB_ORG_API_KEY", "")

    from modules.reminders.cron import delete_job

    result = delete_job("job123")

    assert result is False


@pytest.mark.unit
def test_delete_job_api_failure(monkeypatch):
    monkeypatch.setattr("modules.reminders.cron.CRONJOB_ORG_API_KEY", "test-key")

    with patch("modules.reminders.cron.httpx.delete", side_effect=Exception("fail")):
        from modules.reminders.cron import delete_job

        result = delete_job("job123")

        assert result is False
