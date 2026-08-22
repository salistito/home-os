def migrate(conn):
    cols = [
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(fitness_exercise_entries)"
        ).fetchall()
    ]
    if "metrics" not in cols:
        conn.execute(
            "ALTER TABLE fitness_exercise_entries "
            "ADD COLUMN metrics TEXT NOT NULL DEFAULT '{}'"
        )
