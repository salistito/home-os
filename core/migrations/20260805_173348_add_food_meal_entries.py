def migrate(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS food_meal_entries (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            meal_type  TEXT NOT NULL,
            macros     TEXT NOT NULL DEFAULT '{}',
            notes      TEXT,
            eaten_at   TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_food_meal_entries_user
        ON food_meal_entries(user_id);

        CREATE INDEX IF NOT EXISTS idx_food_meal_entries_eaten_at
        ON food_meal_entries(eaten_at);

        CREATE TABLE IF NOT EXISTS food_meal_entry_items (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            meal_entry_id INTEGER NOT NULL,
            source        TEXT NOT NULL CHECK (source IN ('cook_event', 'manual')),
            name          TEXT NOT NULL,
            macros        TEXT NOT NULL DEFAULT '{}',
            cook_event_id INTEGER,
            portions      REAL CHECK(portions > 0),
            FOREIGN KEY (meal_entry_id) REFERENCES food_meal_entries(id) ON DELETE CASCADE,
            FOREIGN KEY (cook_event_id) REFERENCES food_cook_events(id)
        );

        CREATE INDEX IF NOT EXISTS idx_food_meal_entry_items_entry
        ON food_meal_entry_items(meal_entry_id);
        """
    )
