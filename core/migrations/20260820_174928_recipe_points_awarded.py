from core.utils.string import normalize_string

RECIPES_POINTS = {
    # Triviales: 1 punto si se preparan al menos 2 porciones
    "Café frío": {"points_awarded": 1, "points_min_portions": 2},
    "Matcha frío con leche": {"points_awarded": 1, "points_min_portions": 2},
    "Yogurt con granola y plátano": {"points_awarded": 1, "points_min_portions": 2},
    "Huevos con queso cottage": {"points_awarded": 1, "points_min_portions": 2},
    "Wrap palta jamón queso": {"points_awarded": 1, "points_min_portions": 2},
    # Preparaciones con más pasos: 2-3 puntos si se preparan al menos 2 porciones
    "Papas baby con nuggets": {"points_awarded": 2, "points_min_portions": 2},
    "Charquicán": {"points_awarded": 2, "points_min_portions": 2},
    "Guiso de zapallo italiano": {"points_awarded": 2, "points_min_portions": 2},
    "Humus de betarraga": {"points_awarded": 2, "points_min_portions": 2},
    "Tostadas francesas": {"points_awarded": 2, "points_min_portions": 2},
    "Fideos con carne molida y salsa": {"points_awarded": 2, "points_min_portions": 2},
    "Fajitas": {"points_awarded": 3, "points_min_portions": 2},
    "Quesadillas masivas": {"points_awarded": 3, "points_min_portions": 2},
}


def migrate(conn):
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(food_recipes)").fetchall()]
    if "points_awarded" not in columns:
        conn.execute("ALTER TABLE food_recipes ADD COLUMN points_awarded INTEGER")
    if "points_min_portions" not in columns:
        conn.execute("ALTER TABLE food_recipes ADD COLUMN points_min_portions INTEGER")

    for raw_name, config in RECIPES_POINTS.items():
        name = normalize_string(raw_name)
        cur = conn.execute(
            """
            UPDATE food_recipes
            SET points_awarded = ?,
                points_min_portions = ?
            WHERE name = ?
              AND deleted_at IS NULL
            """,
            (
                config.get("points_awarded"),
                config.get("points_min_portions"),
                name,
            ),
        )
        if cur.rowcount == 0:
            print(f"[migration] recipe not found, skipped: {name!r}")
