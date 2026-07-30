def migrate(conn):
    cur = conn.execute("PRAGMA table_info(food_cook_events)")
    columns = [row[1] for row in cur.fetchall()]

    if "macros" not in columns:
        conn.executescript(
            """
            CREATE TABLE food_cook_events_new (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                user_id   INTEGER NOT NULL,
                portions  INTEGER NOT NULL CHECK(portions >= 1),
                macros    TEXT NOT NULL DEFAULT '{}',
                cooked_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES food_recipes(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            INSERT INTO food_cook_events_new
                (id, recipe_id, portions, cooked_at, created_at)
            SELECT id, recipe_id, portions, cooked_at, created_at
            FROM food_cook_events;

            DROP TABLE food_cook_events;

            ALTER TABLE food_cook_events_new RENAME TO food_cook_events;

            CREATE INDEX IF NOT EXISTS idx_food_cook_events_recipe
            ON food_cook_events(recipe_id);
            """
        )

    if "user_id" not in columns:
        conn.execute(
            "ALTER TABLE food_cook_events ADD COLUMN user_id "
            "INTEGER NOT NULL DEFAULT 1"
        )

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS food_cook_event_ingredients (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            cook_event_id   INTEGER NOT NULL,
            ingredient_id   INTEGER NOT NULL,
            ingredient_name TEXT NOT NULL,
            quantity        REAL NOT NULL CHECK(quantity > 0),
            unit            TEXT NOT NULL,
            macros          TEXT,
            FOREIGN KEY (cook_event_id) REFERENCES food_cook_events(id) ON DELETE CASCADE,
            FOREIGN KEY (ingredient_id) REFERENCES food_ingredients(id)
        );

        CREATE INDEX IF NOT EXISTS idx_food_cook_event_ingredients_event
        ON food_cook_event_ingredients(cook_event_id);

        CREATE INDEX IF NOT EXISTS idx_food_cook_event_ingredients_ingredient
        ON food_cook_event_ingredients(ingredient_id);
        """
    )

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_food_cook_events_user ON food_cook_events(user_id)"
    )
