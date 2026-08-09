def migrate(conn):
    columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(food_meal_entry_items)").fetchall()
    }
    if "ingredient_id" in columns:
        return
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.executescript(
        """
        BEGIN;
        CREATE TABLE food_meal_entry_items_new (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            meal_entry_id INTEGER NOT NULL,
            source        TEXT NOT NULL CHECK (source IN ('cook_event', 'ingredient', 'manual')),
            name          TEXT NOT NULL,
            macros        TEXT NOT NULL DEFAULT '{}',
            cook_event_id INTEGER,
            portions      REAL CHECK(portions > 0),
            ingredient_id INTEGER,
            quantity      REAL CHECK(quantity > 0),
            unit          TEXT,
            FOREIGN KEY (meal_entry_id) REFERENCES food_meal_entries(id) ON DELETE CASCADE,
            FOREIGN KEY (cook_event_id) REFERENCES food_cook_events(id),
            FOREIGN KEY (ingredient_id) REFERENCES food_ingredients(id)
        );
        INSERT INTO food_meal_entry_items_new
            (id, meal_entry_id, source, name, macros, cook_event_id, portions)
            SELECT id, meal_entry_id, source, name, macros, cook_event_id, portions
            FROM food_meal_entry_items;
        DROP TABLE food_meal_entry_items;
        ALTER TABLE food_meal_entry_items_new RENAME TO food_meal_entry_items;
        CREATE INDEX IF NOT EXISTS idx_food_meal_entry_items_entry
        ON food_meal_entry_items(meal_entry_id);
        COMMIT;
        """
    )
    conn.execute("PRAGMA foreign_keys = ON")
