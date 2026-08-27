def migrate(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fitness_exercises (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            kind       TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            deleted_at TEXT
        );
        """
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_active_fitness_exercises_unique_name
        ON fitness_exercises(name)
        WHERE deleted_at IS NULL;
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fitness_routines (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            category    TEXT,
            description TEXT,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL,
            deleted_at  TEXT
        );
        """
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_active_fitness_routines_unique_name
        ON fitness_routines(name)
        WHERE deleted_at IS NULL;
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fitness_routine_exercises (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            routine_id  INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            weight_kg   REAL,
            reps        INTEGER NOT NULL CHECK(reps > 0),
            sets        INTEGER NOT NULL DEFAULT 1 CHECK(sets > 0),
            position    INTEGER NOT NULL,
            FOREIGN KEY (routine_id) REFERENCES fitness_routines(id),
            FOREIGN KEY (exercise_id) REFERENCES fitness_exercises(id),
            UNIQUE(routine_id, exercise_id)
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_routine_exercises_routine
        ON fitness_routine_exercises(routine_id, position);
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fitness_exercise_entries (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            exercise_id     INTEGER,
            routine_id      INTEGER,
            duration_min    INTEGER CHECK(duration_min > 0),
            calories_burned REAL,
            sets_breakdown  TEXT NOT NULL DEFAULT '[]',
            metrics         TEXT NOT NULL DEFAULT '{}',
            notes           TEXT,
            performed_at    TEXT NOT NULL,
            created_at      TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (exercise_id) REFERENCES fitness_exercises(id),
            FOREIGN KEY (routine_id) REFERENCES fitness_routines(id)
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
        CREATE INDEX IF NOT EXISTS idx_fitness_exercise_entries_exercise
        ON fitness_exercise_entries(exercise_id);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_fitness_exercise_entries_routine
        ON fitness_exercise_entries(routine_id);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_fitness_exercise_entries_performed_at
        ON fitness_exercise_entries(performed_at);
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fitness_weight_entries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            weight_kg   REAL NOT NULL CHECK(weight_kg > 0),
            notes       TEXT,
            measured_at TEXT NOT NULL,
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
