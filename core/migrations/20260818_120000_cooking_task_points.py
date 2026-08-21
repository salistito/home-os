import json

COOK_EVENT_TASK_NAME = "Cocinar"
COOK_EVENT_TASK_POINTS = 2
COOK_EVENT_TASK_DELETED_AT = "2026-08-19"
BACKWARD_COMPATIBILITY = "2026-08-01"


def migrate(conn):
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(assignments)").fetchall()]
    if "source" not in columns:
        conn.execute("ALTER TABLE assignments ADD COLUMN source TEXT NOT NULL DEFAULT 'task'")
    if "source_entity_id" not in columns:
        conn.execute("ALTER TABLE assignments ADD COLUMN source_entity_id INTEGER")
    if "source_entity_details" not in columns:
        conn.execute("ALTER TABLE assignments ADD COLUMN source_entity_details TEXT")

    conn.execute("DROP INDEX IF EXISTS idx_one_completed_assignment_per_task_per_day")
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_one_pending_assignment_per_task
        ON assignments(task_id)
        WHERE status = 'pending';
        """
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_one_completed_task_assignment_per_day
        ON assignments(task_id, assigned_at)
        WHERE status = 'completed' AND source = 'task'
        """
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_one_completed_cooking_assignment_per_event
        ON assignments(source_entity_id)
        WHERE status = 'completed' AND source = 'cooking'
        """
    )

    task_row = conn.execute(
        "SELECT id FROM tasks WHERE name = ?", (COOK_EVENT_TASK_NAME,)
    ).fetchone()
    if task_row is None:
        cur = conn.execute(
            """
            INSERT INTO tasks (name, points, frequency_days, next_due_date, deleted_at)
            VALUES (?, ?, NULL, NULL, ?)
            """,
            (COOK_EVENT_TASK_NAME, COOK_EVENT_TASK_POINTS, COOK_EVENT_TASK_DELETED_AT),
        )
        task_id = cur.lastrowid
    else:
        task_id = task_row["id"]

    events = conn.execute(
        """
        SELECT ce.id, ce.user_id, ce.portions, ce.cooked_at, r.category, r.name AS recipe_name
        FROM food_cook_events ce
        JOIN food_recipes r ON r.id = ce.recipe_id
        WHERE ce.portions > 1
          AND substr(ce.cooked_at, 1, 10) >= ?
        """,
        (BACKWARD_COMPATIBILITY,),
    ).fetchall()

    for event in events:
        day = event["cooked_at"][:10]
        details = {
            "recipe_name": event["recipe_name"],
            "recipe_category": event["category"],
            "portions": event["portions"],
            "cooked_at": event["cooked_at"],
        }
        conn.execute(
            """
            INSERT OR IGNORE INTO assignments (
                task_id, user_id, assigned_at, status, completed_at,
                points_awarded, source, source_entity_id, source_entity_details
            )
            VALUES (?, ?, ?, 'completed', ?, ?, 'cooking', ?, ?)
            """,
            (
                task_id,
                event["user_id"],
                day,
                day,
                COOK_EVENT_TASK_POINTS,
                event["id"],
                json.dumps(details),
            ),
        )
