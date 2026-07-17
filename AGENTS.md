# AGENTS.md

- Don't use comments or docstrings in the code.
- For commits, use the conventional commits format: `<type>[optional scope]: <description>` and the commits must be in english.

## Architecture

```
core/   — shared infra (config, DB, schema, utils)
modules/tasks/ — domain logic (service, repository, types)
modules/reminders/ — domain logic (service, repository, types)
modules/users/ — domain logic (service, repository, types)
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
- Import check: `python -c "import core, modules.tasks, modules.reminders, modules.users, apps.bots.telegram; print('imports OK')"`
- No test framework is configured.

## Database migrations

Migration files live in `core/migrations/` and are plain Python files that export a `def migrate(conn):` function.

**Naming convention:** `YYYYMMDD_HHMMSS_short_description.py`
The timestamp prefix ensures natural sort order and uniquely identifies each migration.

**How they run:**
- `core/SCHEMA_VERSION.txt` contains the filename of the last applied migration.
- Every `init_db()` call compares `SCHEMA_VERSION.txt` against the sorted list of migration files.
- Only files with a name *greater* than `SCHEMA_VERSION.txt` are executed.
- After successful application, `SCHEMA_VERSION.txt` is updated to the last file applied.
- If `SCHEMA_VERSION.txt` does not exist (fresh DB / first run), all migrations run.

**Creating a new migration:**
```bash
python scripts/generate_migration.py <description>
```
This creates `core/migrations/<timestamp>_<description>.py` with a `migrate(conn)` stub.

**Important rules:**
- Every migration must be *idempotent* so it is safe to re-run (though in practice
  they only run once because SCHEMA_VERSION tracks them).
- Never edit an already-applied migration. Create a new migration file instead.
- Migrations run inside a single connection; if one fails, the transaction is
  rolled back and SCHEMA_VERSION.txt is NOT updated.

## Telegram bot

- Uses `python-telegram-bot>=21`.
- Handlers: `/start`, `/help`, `/tasks`, `/add_task`, `/list_tasks`, `/edit_task`, `/delete_task`, `/assignments`, `/balance`, `/reminders`, `/add_reminder`, `/list_reminders`, `/edit_reminder`, `/delete_reminder`, text messages (mark assignment done + remind flow), inline keyboard buttons.
- Bot commands are registered in `app.py`.
- Callback data pattern: `assignment_{task_id}|{task_name}`.
- Notifications to Telegram are sent via `python-telegram-bot` API (`reply_text`, `send_message`, `edit_message_text`).

## Production (Fly.io)

- Webhook mode: routes are `POST /telegram` and `GET|POST /trigger-daily/{token}`, `GET|POST /trigger-day-reminders/{token}` and `GET|POST /trigger-timed-reminders/{token}`.
- Web admin API routes: health `GET /api/health`, login `POST /api/login`, tasks CRUD (`POST/GET /api/tasks`, `PATCH/DELETE /api/tasks/{id}`), tasks views (`GET /api/tasks/ranking`, `/api/tasks/daily-breakdown`, `/api/tasks/today-board`), reminders CRUD, finances CRUD, users list (`GET /api/users`).
- No scheduler in-process. Daily assignments and reminders triggered by external cron (e.g. cron-job.org).
- Machine autostops/autostarts (`auto_stop_machines = 'stop'`, `min_machines_running = 0`).
- DB persists in `/app/data/homeos.db` via Fly volume `homeos_data`.
