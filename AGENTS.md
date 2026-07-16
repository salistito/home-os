# AGENTS.md

- Don't use comments or docstrings in the code.
- For commits, use the conventional commits format: `<type>[optional scope]: <description>` and the commits must be in english.

## Architecture

```
core/   — shared infra (DB, config, identity, utils)
modules/tasks/ — domain logic (service, repository, types)
modules/reminders/ — domain logic (service, repository, types)
apps/bots/telegram/ — Telegram bot entrypoint
apps/web/api/ — REST API for web frontend
```

- `core/` must NOT import from `modules/` or `apps/`.
- `modules/` may import from `core/` only.
- `apps/` may import from both.

## Entrypoint

- **Local dev:** `python -m apps.bots.telegram.main` — runs in polling mode if `WEBHOOK_URL` and `WEBHOOK_SECRET` are not set, webhook mode otherwise.
- **Docker:** `docker compose up --build` (Dockerfile at `apps/bots/telegram/Dockerfile`).
- DB is SQLite, auto-initialized on startup (`init_db()` + `load_seed()`).
- Seed data lives in `seed/users.yaml` and `seed/tasks.yaml`; `telegram_chat_id` values support `$ENV_VAR` expansion.

## Commands & verification

- `pip install -e ".[dev]"` — installs project + dev deps (ruff). On Windows, `tzdata` is required for timezone support (auto-installed as a dependency).
- Ruff linter only (no typechecker configured): `ruff check .` (line-length=100).
- Import check: `python -c "import core, modules.tasks, modules.reminders, apps.bots.telegram; print('imports OK')"`
- No test framework is configured.

## Telegram bot

- Uses `python-telegram-bot>=21`.
- Handlers: `/start`, `/help`, `/tasks`, `/add_task`, `/list_tasks`, `/edit_task`, `/delete_task`, `/assignments`, `/balance`, `/reminders`, `/add_reminder`, `/list_reminders`, `/edit_reminder`, `/delete_reminder`, text messages (mark assignment done + remind flow), inline keyboard buttons.
- Bot commands are registered in `app.py`.
- Callback data pattern: `assignment_{task_id}|{task_name}`.
- Notifications to Telegram are sent via `python-telegram-bot` API (`reply_text`, `send_message`, `edit_message_text`).

## Production (Fly.io)

- Webhook mode: routes are `POST /telegram` and `GET|POST /trigger-daily/{token}`, `GET|POST /trigger-day-reminders/{token}` and `GET|POST /trigger-timed-reminders/{token}`.
- No scheduler in-process. Daily assignments and reminders triggered by external cron (e.g. cron-job.org).
- Machine autostops/autostarts (`auto_stop_machines = 'stop'`, `min_machines_running = 0`).
- DB persists in `/app/data/homeos.db` via Fly volume `homeos_data`.
