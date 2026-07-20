# AGENTS.md

- Don't use comments or docstrings in the code.
- For commits, use the conventional commits format: `<type>[optional scope]: <description>` and the commits must be in english.

## Architecture

```
apps/bots/telegram/ — Telegram bot entrypoint
apps/web/api/ — REST API for web frontend
core/   — shared infra (config, DB, schema, utils)
modules/finances/ — domain logic (service, repository, types)
modules/reminders/ — domain logic (service, repository, types)
modules/tasks/ — domain logic (service, repository, types)
modules/users/ — domain logic (service, repository, types)
```

- `core/` must NOT import from `modules/` or `apps/`.
- `modules/` may import from `core/` only.
- `apps/` may import from both.

## Entrypoint

- **Local dev:** `python -m apps.bots.telegram.main` — runs in polling mode if `WEBHOOK_URL` and `WEBHOOK_SECRET` are not set, webhook mode otherwise.
- **Docker:** `docker compose up --build` (Dockerfile at `apps/bots/telegram/Dockerfile`).
- DB is SQLite, auto-initialized on startup (`init_db()`). Users are self-registered via Telegram bot or REST API.
- **User identity:** `users.id` is `INTEGER PRIMARY KEY AUTOINCREMENT` (internal identifier, used as JWT `sub` and in all FKs: `assignments.user_id`, `reminders.user_id`, `finances_entries.owner_id`). `users.name` is `TEXT NOT NULL UNIQUE` (the human login credential, alongside `password_hash`). `telegram_chat_id` is optional (only set for users created via Telegram or `/join`). `role` is `'admin'` or `'member'` — the first user is admin, subsequent users are members. `users.deleted_at` enables soft-delete (users are deactivated, not physically removed). Web login exchanges `{name, password}` for `{token, id, name, role}` where `id` is the integer PK used as JWT `sub` and in all FKs: `assignments.user_id`, `reminders.user_id`, `finances_entries.owner_id`. The frontend persists `{token, userId, userName, userRole}` in localStorage under `homeos_auth`. Deleted users remain visible in historical data but cannot receive new tasks/entries/reminders. The last admin cannot be deleted.

## Commands & verification

- `pip install -e ".[dev]"` — installs project + dev deps (ruff). On Windows, `tzdata` is required for timezone support (auto-installed as a dependency).
- Ruff linter only (no typechecker configured): `ruff check .` (line-length=100).
- Import check: `python -c "from modules.users.repository import get_users; from modules.tasks.service import get_daily_assignments; from modules.reminders.service import create_reminder; from modules.finances.service import open_period; print('imports OK')"`
- Frontend typecheck: `npm run typecheck` (vue-tsc --noEmit) from `apps/web/frontend/`.
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

**Development workflow:**
- `SCHEMA_VERSION.txt` is **never edited manually**. It is updated automatically by
  `init_db()` after applying pending migrations.
- **Fresh DB:** delete `homeos.db`. With no DB and no `SCHEMA_VERSION.txt`, all
  migrations run in order.
- **Existing DB with a new migration you just created:** reset `SCHEMA_VERSION.txt`
  to the filename of the **last previously applied** migration (the one right before
  yours). On next `init_db()`, your new file will be detected as "greater" and applied.
  Setting it to your new filename would mark it as already applied and skip it.
- **Production:** the file is committed with the last production-applied migration.
  On deploy, `init_db()` applies any new migration files automatically and updates
  `SCHEMA_VERSION.txt` in place.

**Important rules:**
- Every migration must be *idempotent* so it is safe to re-run (though in practice
  they only run once because SCHEMA_VERSION tracks them).
- Never edit an already-applied migration. Create a new migration file instead.
- Migrations run inside a single connection; if one fails, the transaction is
  rolled back and SCHEMA_VERSION.txt is NOT updated.

## Telegram bot

- Uses `python-telegram-bot>=21`.
- Handlers: `/start`, `/help`, `/init_home`, `/add_member`, `/join`, `/tasks`, `/add_task`, `/list_tasks`, `/edit_task`, `/delete_task`, `/assignments`, `/balance`, `/reminders`, `/add_reminder`, `/list_reminders`, `/edit_reminder`, `/delete_reminder`, text messages (mark assignment done + remind flow), inline keyboard buttons.
- Bot commands are registered in `app.py`.
- Callback data pattern: `assignment_{task_id}|{task_name}`.
- Notifications to Telegram are sent via `python-telegram-bot` API (`reply_text`, `send_message`, `edit_message_text`).

## Production (Fly.io)

- Webhook mode: routes are `POST /telegram` and `GET|POST /trigger-daily/{token}`, `GET|POST /trigger-day-reminders/{token}` and `GET|POST /trigger-timed-reminders/{token}`.
- Web admin API routes: health `GET /api/health`, login `POST /api/login` (body `{name, password}`, returns `{token, id, name, role}`), users CRUD (`POST /api/register` with `{name, password?, telegram_chat_id?}` — public when no users exist, admin-only otherwise; `GET /api/users`, `PATCH/DELETE /api/users/{id:int}` — admin-only, last admin cannot be deleted), tasks CRUD (`POST/GET /api/tasks`, `PATCH/DELETE /api/tasks/{id}`), tasks views (`GET /api/tasks/ranking`, `/api/tasks/daily-breakdown`, `/api/tasks/today-board`), reminders CRUD, finances CRUD.
- No scheduler in-process. Daily assignments and reminders triggered by external cron (e.g. cron-job.org).
- Machine autostops/autostarts (`auto_stop_machines = 'stop'`, `min_machines_running = 0`).
- DB persists in `/app/data/homeos.db` via Fly volume `homeos_data`.
