import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.unit
class TestMain:
    @pytest.mark.asyncio
    async def test_main_missing_token_raises_system_exit(self, monkeypatch):
        monkeypatch.setattr("apps.bots.telegram.main.TELEGRAM_BOT_TOKEN", "")
        from apps.bots.telegram.main import main
        with pytest.raises(SystemExit, match="TELEGRAM_BOT_TOKEN"):
            await main()

    @pytest.mark.asyncio
    async def test_main_calls_init_db(self, monkeypatch):
        monkeypatch.setattr("apps.bots.telegram.main.TELEGRAM_BOT_TOKEN", "dummy")
        monkeypatch.setattr("apps.bots.telegram.main.WEBHOOK_URL", "")
        monkeypatch.setattr("apps.bots.telegram.main.WEBHOOK_SECRET", "")

        mock_app = MagicMock()
        mock_build_app = MagicMock(return_value=mock_app)

        with (
            patch("apps.bots.telegram.main.init_db") as mock_init,
            patch("apps.bots.telegram.main.build_app", mock_build_app),
            patch("apps.bots.telegram.main._run_polling", AsyncMock()),
        ):
            from apps.bots.telegram.main import main
            await main()

        mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_chooses_webhook_when_url_and_secret_set(self, monkeypatch):
        monkeypatch.setattr("apps.bots.telegram.main.TELEGRAM_BOT_TOKEN", "dummy")
        monkeypatch.setattr("apps.bots.telegram.main.WEBHOOK_URL", "https://example.com")
        monkeypatch.setattr("apps.bots.telegram.main.WEBHOOK_SECRET", "secret")

        with (
            patch("apps.bots.telegram.main.init_db"),
            patch("apps.bots.telegram.main.build_app"),
            patch("apps.bots.telegram.main._run_webhook", AsyncMock()) as mock_webhook,
            patch("apps.bots.telegram.main._run_polling", AsyncMock()) as mock_polling,
        ):
            from apps.bots.telegram.main import main
            await main()

        mock_webhook.assert_called_once()
        mock_polling.assert_not_called()

    @pytest.mark.asyncio
    async def test_main_chooses_polling_when_no_webhook_config(self, monkeypatch):
        monkeypatch.setattr("apps.bots.telegram.main.TELEGRAM_BOT_TOKEN", "dummy")
        monkeypatch.setattr("apps.bots.telegram.main.WEBHOOK_URL", "")
        monkeypatch.setattr("apps.bots.telegram.main.WEBHOOK_SECRET", "")

        with (
            patch("apps.bots.telegram.main.init_db"),
            patch("apps.bots.telegram.main.build_app"),
            patch("apps.bots.telegram.main._run_webhook", AsyncMock()) as mock_webhook,
            patch("apps.bots.telegram.main._run_polling", AsyncMock()) as mock_polling,
        ):
            from apps.bots.telegram.main import main
            await main()

        mock_polling.assert_called_once()
        mock_webhook.assert_not_called()
