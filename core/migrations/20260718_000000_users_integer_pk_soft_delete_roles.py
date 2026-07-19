def migrate(conn):
    rows = conn.execute("PRAGMA table_info(users)").fetchall()
    id_col = next((row for row in rows if row["name"] == "id"), None)
    deleted_at_col = next((row for row in rows if row["name"] == "deleted_at"), None)
    role_col = next((row for row in rows if row["name"] == "role"), None)
    if (
        id_col is not None
        and id_col["type"].upper() == "INTEGER"
        and deleted_at_col is not None
        and role_col is not None
    ):
        return

    conn.executescript("PRAGMA foreign_keys=OFF;")

    conn.execute(
        """
        CREATE TABLE users_new (
          id               INTEGER PRIMARY KEY AUTOINCREMENT,
          name             TEXT NOT NULL UNIQUE,
          role             TEXT NOT NULL DEFAULT 'member',
          password_hash    TEXT,
          telegram_chat_id TEXT,
          deleted_at       TEXT
        )
        """
    )

    old_rows = conn.execute(
        "SELECT id AS old_id, name, password_hash, telegram_chat_id FROM users ORDER BY rowid"
    ).fetchall()
    mapping = {}
    for old in old_rows:
        cur = conn.execute(
            """
            INSERT INTO users_new (name, role, password_hash, telegram_chat_id)
            VALUES (?, 'member', ?, ?)
            """,
            (old["name"], old["password_hash"], old["telegram_chat_id"]),
        )
        mapping[old["old_id"]] = cur.lastrowid

    first = conn.execute("SELECT MIN(id) FROM users_new").fetchone()
    if first and first[0] is not None:
        conn.execute("UPDATE users_new SET role = 'admin' WHERE id = ?", first)

    conn.executescript(
        """
        CREATE TABLE assignments_new (
          id             INTEGER PRIMARY KEY AUTOINCREMENT,
          task_id        INTEGER NOT NULL,
          user_id        INTEGER NOT NULL,
          assigned_at    TEXT NOT NULL,
          status         TEXT NOT NULL DEFAULT 'pending'
                         CHECK (status IN ('pending', 'completed', 'failed')),
          completed_at   TEXT,
          points_awarded INTEGER,
          FOREIGN KEY (task_id) REFERENCES tasks(id),
          FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    a_rows = conn.execute(
        """
        SELECT id, task_id, user_id, assigned_at, status, completed_at, points_awarded
        FROM assignments ORDER BY id
        """
    ).fetchall()
    for r in a_rows:
        new_user_id = mapping.get(r["user_id"]) if r["user_id"] is not None else None
        if new_user_id is None:
            continue
        conn.execute(
            """
            INSERT INTO assignments_new
                (id, task_id, user_id, assigned_at, status, completed_at, points_awarded)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                r["id"],
                r["task_id"],
                new_user_id,
                r["assigned_at"],
                r["status"],
                r["completed_at"],
                r["points_awarded"],
            ),
        )

    conn.executescript(
        """
        CREATE TABLE reminders_new (
          id           INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id      INTEGER NOT NULL,
          message      TEXT NOT NULL,
          trigger_at   TEXT NOT NULL,
          trigger_time TEXT,
          recurrence   TEXT NOT NULL DEFAULT 'none'
                        CHECK (recurrence IN ('none', 'daily', 'weekly', 'monthly', 'yearly')),
          cron_job_id  TEXT,
          created_at   TEXT NOT NULL,
          FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    r_rows = conn.execute(
        """
        SELECT id, user_id, message, trigger_at, trigger_time, recurrence, cron_job_id, created_at
        FROM reminders ORDER BY id
        """
    ).fetchall()
    for r in r_rows:
        conn.execute(
            """
            INSERT INTO reminders_new
                (id, user_id, message, trigger_at, trigger_time, recurrence, cron_job_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                r["id"],
                mapping[r["user_id"]],
                r["message"],
                r["trigger_at"],
                r["trigger_time"],
                r["recurrence"],
                r["cron_job_id"],
                r["created_at"],
            ),
        )

    conn.executescript(
        """
        CREATE TABLE finances_entries_new (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          period_id   INTEGER NOT NULL,
          kind        TEXT NOT NULL CHECK (kind IN ('income', 'expense')),
          scope       TEXT NOT NULL CHECK (scope IN ('shared', 'personal')),
          owner_id    INTEGER NOT NULL,
          label       TEXT NOT NULL,
          amount      INTEGER,
          status      TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'confirmed')),
          paid_at     TEXT,
          detail_mode TEXT NOT NULL DEFAULT 'none'
                        CHECK (detail_mode IN ('none', 'top_down', 'bottom_up')),
          created_at  TEXT NOT NULL,
          FOREIGN KEY (period_id) REFERENCES finances_periods(id),
          FOREIGN KEY (owner_id)  REFERENCES users(id)
        );
        """
    )
    e_rows = conn.execute(
        """
        SELECT id, period_id, kind, scope, owner_id, label, amount,
               status, paid_at, detail_mode, created_at
        FROM finances_entries ORDER BY id
        """
    ).fetchall()
    for r in e_rows:
        conn.execute(
            """
            INSERT INTO finances_entries_new
                (id, period_id, kind, scope, owner_id, label, amount,
                 status, paid_at, detail_mode, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                r["id"],
                r["period_id"],
                r["kind"],
                r["scope"],
                mapping[r["owner_id"]],
                r["label"],
                r["amount"],
                r["status"],
                r["paid_at"],
                r["detail_mode"],
                r["created_at"],
            ),
        )

    conn.executescript(
        """
        DROP TABLE assignments;
        ALTER TABLE assignments_new RENAME TO assignments;

        CREATE UNIQUE INDEX IF NOT EXISTS idx_one_pending_assignment_per_task
        ON assignments(task_id)
        WHERE status = 'pending';

        CREATE UNIQUE INDEX IF NOT EXISTS idx_one_completed_assignment_per_task_per_day
        ON assignments(task_id, assigned_at)
        WHERE status = 'completed';

        DROP TABLE reminders;
        ALTER TABLE reminders_new RENAME TO reminders;

        CREATE UNIQUE INDEX IF NOT EXISTS idx_user_reminders_unique_message
        ON reminders(user_id, message);

        CREATE INDEX IF NOT EXISTS idx_reminders_pending_due
        ON reminders(trigger_at);

        DROP TABLE finances_entries;
        ALTER TABLE finances_entries_new RENAME TO finances_entries;

        CREATE INDEX IF NOT EXISTS idx_finances_entries_period
        ON finances_entries(period_id);

        DROP TABLE users;
        ALTER TABLE users_new RENAME TO users;

        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_unique_name
        ON users(name);

        PRAGMA foreign_keys=ON;
        """
    )
