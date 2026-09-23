def migrate(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS break_periods (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            label      TEXT,
            start_date TEXT NOT NULL,
            end_date   TEXT,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_break_periods_dates
        ON break_periods(start_date, end_date);
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS break_users (
            break_period_id INTEGER NOT NULL,
            user_id         INTEGER NOT NULL,
            PRIMARY KEY (break_period_id, user_id),
            FOREIGN KEY (break_period_id) REFERENCES break_periods(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id)  REFERENCES users(id)
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_break_users_break_period
        ON break_users(break_period_id);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_break_users_user
        ON break_users(user_id);
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS break_modules (
            break_period_id INTEGER NOT NULL,
            module          TEXT NOT NULL,
            PRIMARY KEY (break_period_id, module),
            FOREIGN KEY (break_period_id) REFERENCES break_periods(id) ON DELETE CASCADE
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_break_modules_break_period
        ON break_modules(break_period_id);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_break_modules_module
        ON break_modules(module);
        """
    )
