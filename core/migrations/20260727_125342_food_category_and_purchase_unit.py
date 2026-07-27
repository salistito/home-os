import sqlite3


def migrate(conn):
    for stmt in [
        "ALTER TABLE food_ingredients ADD COLUMN purchase_unit TEXT",
        "ALTER TABLE food_ingredients ADD COLUMN purchase_conversion_factor REAL",
        "ALTER TABLE food_recipes ADD COLUMN category TEXT",
    ]:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            pass
