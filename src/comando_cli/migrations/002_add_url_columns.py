"""Add title_url and magnet_url columns."""

from yoyo import step


def add_column_if_not_exists(backend):
    """Add columns if they don't already exist."""
    cursor = backend.cursor()
    try:
        # Check if title_url column exists
        cursor.execute("PRAGMA table_info(watch_history)")
        columns = {row[1] for row in cursor.fetchall()}

        if "title_url" not in columns:
            cursor.execute("ALTER TABLE watch_history ADD COLUMN title_url TEXT")
        if "magnet_url" not in columns:
            cursor.execute("ALTER TABLE watch_history ADD COLUMN magnet_url TEXT")
    finally:
        cursor.close()


def drop_columns_if_exist(backend):
    """Drop columns if they exist."""
    cursor = backend.cursor()
    try:
        cursor.execute("PRAGMA table_info(watch_history)")
        columns = {row[1] for row in cursor.fetchall()}

        if "title_url" in columns:
            cursor.execute("ALTER TABLE watch_history DROP COLUMN title_url")
        if "magnet_url" in columns:
            cursor.execute("ALTER TABLE watch_history DROP COLUMN magnet_url")
    finally:
        cursor.close()


steps = [
    step(add_column_if_not_exists, drop_columns_if_exist),
]
