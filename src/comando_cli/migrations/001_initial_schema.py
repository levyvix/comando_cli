"""Initial schema creation."""

from yoyo import step

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS watch_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title_id TEXT NOT NULL,
            title_name TEXT NOT NULL,
            media_type TEXT NOT NULL,
            last_episode INTEGER,
            last_watched_date DATETIME NOT NULL,
            duration_seconds INTEGER DEFAULT 0,
            position_seconds INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(title_id)
        )
        """,
        "DROP TABLE IF EXISTS watch_history",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS idx_title_id ON watch_history(title_id)",
        "DROP INDEX IF EXISTS idx_title_id",
    ),
    step(
        "CREATE INDEX IF NOT EXISTS idx_last_watched ON watch_history(last_watched_date DESC)",
        "DROP INDEX IF EXISTS idx_last_watched",
    ),
]
