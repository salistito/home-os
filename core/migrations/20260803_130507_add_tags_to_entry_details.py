def migrate(conn):
    tables = [
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    ]
    if "finances_entry_detail_tags" in tables:
        return

    conn.execute(
        """
        CREATE TABLE finances_entry_detail_tags (
          detail_id INTEGER NOT NULL,
          tag_id    INTEGER NOT NULL,

          PRIMARY KEY (detail_id, tag_id),
          FOREIGN KEY (detail_id) REFERENCES finances_entry_details(id) ON DELETE CASCADE,
          FOREIGN KEY (tag_id)    REFERENCES finances_tags(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_finances_entry_detail_tags_tag "
        "ON finances_entry_detail_tags(tag_id)"
    )
