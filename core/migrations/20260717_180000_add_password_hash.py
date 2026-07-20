def migrate(conn):
    rows = conn.execute("PRAGMA table_info(users)").fetchall()
    if any(row["name"] == "password_hash" for row in rows):
        return
    conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
