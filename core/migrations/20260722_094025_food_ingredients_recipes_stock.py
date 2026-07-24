def migrate(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS food_ingredients (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            category        TEXT,
            unit            TEXT NOT NULL,
            macros          TEXT NOT NULL DEFAULT '{}',
            external_source TEXT,
            external_id     TEXT,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL,
            deleted_at      TEXT
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_active_food_ingredients_unique_name
        ON food_ingredients(name)
        WHERE deleted_at IS NULL;

        CREATE TABLE IF NOT EXISTS food_stock (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_id      INTEGER NOT NULL,
            quantity           REAL NOT NULL CHECK(quantity >= 0),
            min_alert_quantity REAL NOT NULL DEFAULT 0,
            expiration_date    TEXT,
            updated_at         TEXT NOT NULL,
            FOREIGN KEY (ingredient_id) REFERENCES food_ingredients(id)
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_food_stock_ingredient
        ON food_stock(ingredient_id);

        CREATE TABLE IF NOT EXISTS food_purchases (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_id INTEGER NOT NULL,
            quantity      REAL NOT NULL CHECK(quantity > 0),
            price         INTEGER NOT NULL CHECK(price >= 0),
            purchased_at  TEXT NOT NULL,
            notes         TEXT,
            created_at    TEXT NOT NULL,
            FOREIGN KEY (ingredient_id) REFERENCES food_ingredients(id)
        );

        CREATE INDEX IF NOT EXISTS idx_food_purchases_ingredient
        ON food_purchases(ingredient_id);

        CREATE TABLE IF NOT EXISTS food_recipes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            description TEXT,
            portions    INTEGER NOT NULL CHECK(portions >= 1),
            steps       TEXT,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL,
            deleted_at  TEXT
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_active_food_recipes_unique_name
        ON food_recipes(name)
        WHERE deleted_at IS NULL;

        CREATE TABLE IF NOT EXISTS food_recipe_ingredients (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id     INTEGER NOT NULL,
            ingredient_id INTEGER NOT NULL,
            quantity      REAL NOT NULL CHECK(quantity > 0),
            unit          TEXT NOT NULL,
            FOREIGN KEY (recipe_id) REFERENCES food_recipes(id) ON DELETE CASCADE,
            FOREIGN KEY (ingredient_id) REFERENCES food_ingredients(id)
        );

        CREATE INDEX IF NOT EXISTS idx_food_recipe_ingredients_recipe
        ON food_recipe_ingredients(recipe_id);

        CREATE INDEX IF NOT EXISTS idx_food_recipe_ingredients_ingredient
        ON food_recipe_ingredients(ingredient_id);

        CREATE TABLE IF NOT EXISTS food_cook_events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            portions  INTEGER NOT NULL CHECK(portions >= 1),
            cooked_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (recipe_id) REFERENCES food_recipes(id)
        );

        CREATE INDEX IF NOT EXISTS idx_food_cook_events_recipe
        ON food_cook_events(recipe_id);
        """
    )
