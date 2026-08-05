def migrate(conn):
    detail_columns = [
        row["name"]
        for row in conn.execute("PRAGMA table_info(finances_entry_details)").fetchall()
    ]
    if detail_columns != ["id", "entry_id", "scope", "label", "amount"]:
        scope_source = "scope" if "scope" in detail_columns else "NULL"
        conn.executescript(
            f"""
            PRAGMA foreign_keys=OFF;

            CREATE TABLE finances_entry_details_new (
              id       INTEGER PRIMARY KEY AUTOINCREMENT,
              entry_id INTEGER NOT NULL,
              scope    TEXT,
              label    TEXT NOT NULL,
              amount   INTEGER NOT NULL DEFAULT 0,
              FOREIGN KEY (entry_id) REFERENCES finances_entries(id) ON DELETE CASCADE
            );

            INSERT INTO finances_entry_details_new (id, entry_id, scope, label, amount)
            SELECT id, entry_id, {scope_source}, label, amount
            FROM finances_entry_details
            ORDER BY id;

            DROP TABLE finances_entry_details;
            ALTER TABLE finances_entry_details_new RENAME TO finances_entry_details;

            CREATE INDEX IF NOT EXISTS idx_finances_entry_details_entry
            ON finances_entry_details(entry_id);

            PRAGMA foreign_keys=ON;
            """
        )

    row = conn.execute(
        """
        SELECT sql FROM sqlite_master
        WHERE type = 'table' AND name = 'finances_entries'
        """
    ).fetchone()
    if row is None or "mixed" in row["sql"]:
        return

    conn.executescript(
        """
        PRAGMA foreign_keys=OFF;

        CREATE TABLE finances_entries_new (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          period_id   INTEGER NOT NULL,
          kind        TEXT NOT NULL CHECK (kind IN ('income', 'expense')),
          scope       TEXT NOT NULL CHECK (scope IN ('shared', 'personal', 'mixed')),
          owner_id    INTEGER NOT NULL,
          label       TEXT NOT NULL,
          amount      INTEGER,
          status      TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'confirmed')),
          paid_at     TEXT,
          detail_mode TEXT NOT NULL DEFAULT 'none'
                        CHECK (detail_mode IN ('none', 'top_down', 'bottom_up')),
          created_at  TEXT NOT NULL,
          FOREIGN KEY (period_id) REFERENCES finances_periods(id),
          FOREIGN KEY (owner_id)  REFERENCES users(id)
        );

        INSERT INTO finances_entries_new SELECT * FROM finances_entries;
        DROP TABLE finances_entries;
        ALTER TABLE finances_entries_new RENAME TO finances_entries;

        CREATE INDEX IF NOT EXISTS idx_finances_entries_period
        ON finances_entries(period_id);

        PRAGMA foreign_keys=ON;
        """
    )
