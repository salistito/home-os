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
