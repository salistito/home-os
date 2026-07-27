def migrate(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS food_nutrition_goals (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          INTEGER NOT NULL,
            kcal_target      INTEGER,
            protein_g_target REAL,
            carbs_g_target   REAL,
            fat_g_target     REAL,
            updated_at       TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id)
        );
        """
    )
