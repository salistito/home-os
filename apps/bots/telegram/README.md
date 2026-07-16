# Telegram bot

Household task and reminder management bot built with `python-telegram-bot>=21`.

## Getting your `telegram_chat_id`

Each person has a numeric `chat_id` (e.g. `123456789`) that Telegram assigns to their conversation with the bot. The bot uses it to send messages.

How to get it:

- Message `@userinfobot` or `@getidsbot` on Telegram; they reply with your `chat_id`.

## Getting the bot token

Talk to `@BotFather`, create a bot with `/newbot`, and copy the token to the `TELEGRAM_BOT_TOKEN` env var (see `.env.example`).

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot API token from BotFather |
| `WEBHOOK_URL` | No | Base URL for webhook mode (e.g. `https://homeos.fly.dev`). If empty, runs in polling mode |
| `WEBHOOK_SECRET` | No | Shared secret for validating Telegram updates and trigger endpoints |
| `CRONJOB_ORG_API_KEY` | No | cron-job.org API key for timed reminder scheduling |
| `PORT` | No | Webhook server port (default: `8080`) |

## Running

- **Local dev:** `python -m apps.bots.telegram.main` — runs in polling mode if `WEBHOOK_URL` and `WEBHOOK_SECRET` are not set, webhook mode otherwise.
- **Docker:** `docker compose up --build` (Dockerfile at `apps/bots/telegram/Dockerfile`).

## Bot commands

| Command | Description |
|---|---|
| `/start`, `/help` | Welcome message with command overview |
| `/tasks` | Task management help |
| `/add_task <name> <points> [freq]` | Create a task (freq = days between assignments) |
| `/list_tasks` | List all active tasks |
| `/edit_task <name> <field> <value>` | Edit a task field (`name`, `points`, `freq`) |
| `/delete_task <name>` | Soft-delete a task |
| `/assignments` | Show today's assignments with inline buttons |
| `/balance` | Show monthly score balance |
| `/reminders` | Reminder management help |
| `/add_reminder` | Create a reminder (interactive wizard or inline args) |
| `/list_reminders` | List your reminders |
| `/edit_reminder` | Edit a reminder (interactive wizard or inline args) |
| `/delete_reminder` | Delete a reminder (interactive wizard or inline args) |

### Reminder wizards

Commands `/add_reminder`, `/edit_reminder`, and `/delete_reminder` support both inline arguments and multi-step interactive wizards. If called without arguments, the bot guides the user through prompts.

Supported time formats for reminders:

- Relative: `45m`, `1h30m`, `4h`, `3d`, `2w`
- Absolute: `2025-07-15` or `2025-07-15 14:30`

Recurrence options: `none`, `daily`, `weekly`, `monthly`, `yearly`.

### Assignment buttons

The `/assignments` command shows an inline keyboard. Tapping a button marks the task as done and updates the list in-place.

Callback data format: `assignment_{task_id}|{task_name}`

## Webhook routes

When running in webhook mode, the following HTTP routes are exposed via Starlette:

| Method | Path | Description |
|---|---|---|
| `POST` | `/telegram` | Receives Telegram updates. Validates `X-Telegram-Bot-Api-Secret-Token` header |
| `GET`/`POST` | `/trigger_daily_assignments/{token}` | Triggers daily assignment notifications (token = `WEBHOOK_SECRET`) |
| `GET`/`POST` | `/trigger_day_reminders/{token}` | Triggers due untimed reminder notifications |
| `GET`/`POST` | `/trigger_timed_reminders/{token}` | Triggers due timed reminder notifications |

External cron services (e.g. cron-job.org) should call these endpoints on schedule.

## Background jobs

| Job | Description |
|---|---|
| `send_daily_assignments` | Fails stale pending assignments, generates today's assignments, sends each user their morning message with inline keyboard |
| `send_day_reminders` | Sends due untimed reminders, then deletes non-recurring or advances recurrence |
| `send_timed_reminders` | Sends due timed reminders, then deletes non-recurring or advances recurrence |

## Handler architecture

```
handlers/
  commands.py          — All 14 command handlers
  messages.py          — Text message handler + assignment button callback
  utils/
    tasks.py           — Task argument parsing and reply builders
    reminders.py       — Reminder argument parsing, reply builders, and wizard handlers
```

- `commands.py` uses a `@require_registration` decorator to gate commands behind user registration.
- Reminder wizards track step state in `context.user_data["*_step"]`.
- `messages.py` routes incoming text to the appropriate wizard or to `mark_assignment_done`.
