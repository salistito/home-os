def migrate(conn):
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'reminders'"
    ).fetchone()
    if row is None or "CHECK (recurrence IN" not in row["sql"]:
        return

    conn.executescript(
        """
        CREATE TABLE reminders_new (
          id                  INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id             INTEGER NOT NULL,
          message             TEXT NOT NULL,
          trigger_at          TEXT NOT NULL,
          trigger_time        TEXT,
          recurrence          TEXT NOT NULL DEFAULT 'none',
          cron_job_id         TEXT,
          created_at          TEXT NOT NULL,
          owner               TEXT NOT NULL DEFAULT 'user' CHECK (owner IN ('user', 'system')),
          system_ref_entity   TEXT,
          system_ref_entity_id TEXT,
          FOREIGN KEY (user_id) REFERENCES users(id)
        );

        INSERT INTO reminders_new
            (id, user_id, message, trigger_at, trigger_time, recurrence, cron_job_id, created_at,
             owner, system_ref_entity, system_ref_entity_id)
        SELECT id, user_id, message, trigger_at, trigger_time, recurrence, cron_job_id, created_at,
               owner, system_ref_entity, system_ref_entity_id
        FROM reminders;

        DROP TABLE reminders;
        ALTER TABLE reminders_new RENAME TO reminders;

        CREATE UNIQUE INDEX IF NOT EXISTS idx_user_reminders_unique_message
        ON reminders(user_id, message)
        WHERE owner = 'user';

        CREATE INDEX IF NOT EXISTS idx_reminders_pending_due
        ON reminders(trigger_at);

        CREATE INDEX IF NOT EXISTS idx_reminders_system_ref
        ON reminders(owner, system_ref_entity, system_ref_entity_id);
        """
    )
