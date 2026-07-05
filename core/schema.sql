CREATE TABLE IF NOT EXISTS users (
  id               TEXT PRIMARY KEY,
  name             TEXT NOT NULL,
  telegram_chat_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  name           TEXT NOT NULL,
  frequency_days INTEGER,
  points         INTEGER NOT NULL,
  next_due_date  TEXT
);

CREATE TABLE IF NOT EXISTS assignments (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id        INTEGER NOT NULL REFERENCES tasks(id),
  user_id        TEXT REFERENCES users(id),
  assigned_at  TEXT NOT NULL,
  completed_at   TEXT,
  status         TEXT NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending', 'completed', 'failed')),
  points_awarded INTEGER
);
