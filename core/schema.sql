CREATE TABLE IF NOT EXISTS users (
  id               TEXT PRIMARY KEY,
  name             TEXT NOT NULL,
  telegram_chat_id TEXT NOT NULL,
  password_hash    TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  name           TEXT NOT NULL,
  points         INTEGER NOT NULL,
  frequency_days INTEGER,
  next_due_date  TEXT,
  deleted_at     TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_active_tasks_unique_name
ON tasks(name)
WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS assignments (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id        INTEGER NOT NULL,
  user_id        TEXT,
  assigned_at    TEXT NOT NULL,
  status         TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
  completed_at   TEXT,
  points_awarded INTEGER,

  FOREIGN KEY (task_id) REFERENCES tasks(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_pending_assignment_per_task
ON assignments(task_id)
WHERE status = 'pending';

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_completed_assignment_per_task_per_day
ON assignments(task_id, assigned_at)
WHERE status = 'completed';

CREATE TABLE IF NOT EXISTS reminders (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id      TEXT NOT NULL,
  message      TEXT NOT NULL,
  trigger_at   TEXT NOT NULL,
  trigger_time TEXT,
  recurrence   TEXT NOT NULL DEFAULT 'none' CHECK (recurrence IN ('none', 'daily', 'weekly', 'monthly', 'yearly')),
  cron_job_id  TEXT,
  created_at   TEXT NOT NULL,

  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_reminders_unique_message
ON reminders(user_id, message);

CREATE INDEX IF NOT EXISTS idx_reminders_pending_due
ON reminders(trigger_at);

CREATE TABLE IF NOT EXISTS finances_periods (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  label     TEXT NOT NULL,
  status    TEXT NOT NULL DEFAULT 'open'
              CHECK (status IN ('open', 'closed')),
  opened_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_open_period
ON finances_periods(status)
WHERE status = 'open';

CREATE TABLE IF NOT EXISTS finances_entries (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  period_id   INTEGER NOT NULL,
  kind        TEXT NOT NULL CHECK (kind IN ('income', 'expense')),
  scope       TEXT NOT NULL CHECK (scope IN ('shared', 'personal')),
  owner_id    TEXT NOT NULL,
  label       TEXT NOT NULL,
  amount      INTEGER NOT NULL DEFAULT 0,
  status      TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'confirmed', 'rejected')),
  paid_at     TEXT,
  detail_mode TEXT NOT NULL DEFAULT 'none'
                CHECK (detail_mode IN ('none', 'top_down', 'bottom_up')),
  created_at  TEXT NOT NULL,

  FOREIGN KEY (period_id) REFERENCES finances_periods(id),
  FOREIGN KEY (owner_id)  REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_finances_entries_period
ON finances_entries(period_id);

CREATE TABLE IF NOT EXISTS finances_entry_details (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  entry_id INTEGER NOT NULL,
  label    TEXT NOT NULL,
  amount   INTEGER NOT NULL DEFAULT 0,

  FOREIGN KEY (entry_id) REFERENCES finances_entries(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_finances_entry_details_entry
ON finances_entry_details(entry_id);
