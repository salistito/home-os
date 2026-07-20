def migrate(conn):
    rows = conn.execute("PRAGMA table_info(finances_entries)").fetchall()
    amount = next((row for row in rows if row["name"] == "amount"), None)
    if amount is None or amount["notnull"] == 0:
        return

    conn.executescript("""
        PRAGMA foreign_keys=OFF;

        CREATE TABLE finances_entries_new (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          period_id   INTEGER NOT NULL,
          kind        TEXT NOT NULL CHECK (kind IN ('income', 'expense')),
          scope       TEXT NOT NULL CHECK (scope IN ('shared', 'personal')),
          owner_id    TEXT NOT NULL,
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
    """)
