# AGENTS.md

- Don't use comments or docstrings in the code.
- For commits, use the conventional commits format: `<type>[optional scope]: <description>` and the commits must be in english.

## Architecture

```
core/   — shared infra (DB, config, identity, notifications)
modules/tasks/ — domain logic (service, repository, types)
apps/bots/telegram/ — Telegram bot entrypoint
```

- `core/` must NOT import from `modules/` or `apps/`.
- `modules/` may import from `core/` only.
- `apps/` may import from both.

## Entrypoint

- **Local dev:** `python -m apps.bots.telegram.main` — runs in webhook mode (requires `WEBHOOK_URL` and `WEBHOOK_SECRET`).
- **Docker:** `docker compose up --build` (Dockerfile at `apps/bots/telegram/Dockerfile`).
- DB is SQLite, auto-initialized on startup (`init_db()` + `load_seed()`).
- Seed data lives in `seed/users.yaml` and `seed/tasks.yaml`; `telegram_chat_id` values support `$ENV_VAR` expansion.

## Commands & verification

- `pip install -e ".[dev]"` — installs project + dev deps (ruff).
- Ruff linter only (no typechecker configured): `ruff check .` (line-length=100).
- Import check: `python -c "import core, modules.tasks, apps.bots.telegram; print('imports OK')"`
- No test framework is configured.

## Telegram bot

- Uses `python-telegram-bot>=21`.
- Handlers: `/start`, `/balance`, `/tasks`, text messages (mark task done), inline keyboard buttons.
- Bot commands are registered in `app.py`.
- `core/notifications.py` calls Telegram API directly via urllib (not through python-telegram-bot).

## Production (Fly.io)

- Webhook mode: routes are `POST /telegram` and `GET|POST /trigger-daily/{token}`.
- No scheduler in-process. Daily assignments triggered by external cron (e.g. cron-job.org).
- Machine autostops/autostarts (`auto_stop_machines = 'stop'`, `min_machines_running = 0`).
- DB persists in `/app/data/homeos.db` via Fly volume `homeos_data`.
