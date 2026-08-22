def migrate(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fitness_weight_entries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            weight_kg   REAL NOT NULL CHECK(weight_kg > 0),
            measured_at TEXT NOT NULL,
            notes       TEXT,
            created_at  TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, measured_at)
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_fitness_weight_entries_user
        ON fitness_weight_entries(user_id);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_fitness_weight_entries_measured_at
        ON fitness_weight_entries(measured_at);
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fitness_exercise_entries (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            exercise_type   TEXT NOT NULL,
            duration_min    INTEGER CHECK(duration_min > 0),
            intensity       TEXT CHECK(intensity IN ('low', 'medium', 'high')),
            calories_burned REAL,
            performed_at    TEXT NOT NULL,
            notes           TEXT,
            created_at      TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_fitness_exercise_entries_user
        ON fitness_exercise_entries(user_id);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_fitness_exercise_entries_performed_at
        ON fitness_exercise_entries(performed_at);
        """
    )
