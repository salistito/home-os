def migrate(conn):
    existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(reminders)").fetchall()}

    if "owner" not in existing_cols:
        conn.execute("ALTER TABLE reminders ADD COLUMN owner TEXT NOT NULL DEFAULT 'user'")
    if "system_ref_entity" not in existing_cols:
        conn.execute("ALTER TABLE reminders ADD COLUMN system_ref_entity TEXT")
    if "system_ref_entity_id" not in existing_cols:
        conn.execute("ALTER TABLE reminders ADD COLUMN system_ref_entity_id TEXT")

    conn.execute("DROP INDEX IF EXISTS idx_user_reminders_unique_message")

    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_user_reminders_unique_message
        ON reminders(user_id, message)
        WHERE owner = 'user'
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reminders_system_ref
        ON reminders(owner, system_ref_entity, system_ref_entity_id)
        """
    )
