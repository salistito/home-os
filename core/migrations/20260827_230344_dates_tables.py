def migrate(conn):
    # Couples
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS date_couples (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at          TEXT,
            relationship_status TEXT NOT NULL DEFAULT 'couple'
                                CHECK (relationship_status IN ('couple', 'married')),
            status              TEXT NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active', 'archived')),
            created_at          TEXT NOT NULL,
            updated_at          TEXT NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS date_couple_members (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            couple_id INTEGER NOT NULL,
            user_id   INTEGER NOT NULL,
            FOREIGN KEY (couple_id) REFERENCES date_couples(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id)   REFERENCES users(id),
            UNIQUE(couple_id, user_id)
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_date_couple_members_user
        ON date_couple_members(user_id);
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS date_couple_milestones (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            couple_id  INTEGER NOT NULL,
            type       TEXT NOT NULL
                       CHECK (type IN ('monthly', 'anniversary', 'wedding', 'custom')),
            date       TEXT NOT NULL,
            label      TEXT NOT NULL,
            notes      TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (couple_id) REFERENCES date_couples(id) ON DELETE CASCADE
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_date_couple_milestones_couple
        ON date_couple_milestones(couple_id);
        """
    )
    # Dates / events
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS date_events (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            couple_id       INTEGER NOT NULL,
            week_start      TEXT NOT NULL,
            planned_by      INTEGER NOT NULL,
            scheduled_date  TEXT,
            scheduled_time  TEXT,
            title           TEXT,
            status          TEXT NOT NULL DEFAULT 'planned'
                            CHECK (status IN ('planned', 'scheduled', 'done')),
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL,
            FOREIGN KEY (couple_id) REFERENCES date_couples(id) ON DELETE CASCADE,
            FOREIGN KEY (planned_by) REFERENCES users(id),
            UNIQUE(couple_id, week_start)
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_date_events_couple
        ON date_events(couple_id);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_date_events_week_start
        ON date_events(week_start);
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS date_attributes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id   INTEGER NOT NULL,
            key        TEXT NOT NULL,
            value      TEXT NOT NULL,
            is_secret  INTEGER NOT NULL DEFAULT 0,
            reveal_on  TEXT,
            FOREIGN KEY (event_id) REFERENCES date_events(id) ON DELETE CASCADE
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_date_attributes_event
        ON date_attributes(event_id);
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS date_memories (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id   INTEGER NOT NULL,
            kind       TEXT NOT NULL CHECK (kind IN ('photo', 'note')),
            media_url  TEXT,
            caption    TEXT,
            taken_by   INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES date_events(id) ON DELETE CASCADE,
            FOREIGN KEY (taken_by) REFERENCES users(id)
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_date_memories_event
        ON date_memories(event_id);
        """
    )
