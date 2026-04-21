"""Database operations for watch history and metadata storage."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from comando_cli.migrations import run_migrations
from comando_cli.models import MediaType, WatchHistory


class Database:
    """SQLite database for watch history."""

    def __init__(self, db_path: Path):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        run_migrations(self.db_path)

    def add_watch_record(
        self,
        title_id: str,
        title_name: str,
        media_type: MediaType,
        title_url: Optional[str] = None,
        magnet_url: Optional[str] = None,
        last_episode: Optional[int] = None,
        duration_seconds: int = 0,
    ) -> WatchHistory:
        """Add or update a watch history record.

        Args:
            title_id: Unique title identifier
            title_name: Name of the title
            media_type: Type of media (movie/series)
            title_url: Page URL (used to re-fetch series episodes)
            magnet_url: Magnet URL (for movies: skip re-fetch on resume)
            last_episode: Last watched episode (for series)
            duration_seconds: Total duration of the content

        Returns:
            WatchHistory object
        """
        now = datetime.now()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO watch_history (
                    title_id, title_name, media_type, title_url, magnet_url,
                    last_episode, last_watched_date, duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(title_id) DO UPDATE SET
                    title_name = excluded.title_name,
                    title_url = COALESCE(excluded.title_url, title_url),
                    magnet_url = COALESCE(excluded.magnet_url, magnet_url),
                    last_episode = COALESCE(excluded.last_episode, last_episode),
                    last_watched_date = excluded.last_watched_date,
                    duration_seconds = excluded.duration_seconds,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    title_id,
                    title_name,
                    media_type.value,
                    title_url,
                    magnet_url,
                    last_episode,
                    now,
                    duration_seconds,
                ),
            )

            conn.commit()

            record = self.get_watch_record(title_id)
            if not record:
                raise RuntimeError(
                    f"failed to create watch record for title_id {title_id}"
                )
            return record

    def get_watch_record(self, title_id: str) -> Optional[WatchHistory]:
        """Get a watch history record by title ID.

        Args:
            title_id: Unique title identifier

        Returns:
            WatchHistory object or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM watch_history WHERE title_id = ?",
                (title_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_watch_history(row)

    def get_all_watch_history(self) -> list[WatchHistory]:
        """Get all watch history records, ordered by last watched.

        Returns:
            List of WatchHistory objects
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM watch_history ORDER BY last_watched_date DESC"
            )
            rows = cursor.fetchall()

            return [self._row_to_watch_history(row) for row in rows]

    def get_last_watched(self) -> Optional[WatchHistory]:
        """Get the most recently watched title.

        Returns:
            WatchHistory object or None if no history exists
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM watch_history ORDER BY last_watched_date DESC LIMIT 1"
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_watch_history(row)

    def update_position(self, title_id: str, position_seconds: int) -> None:
        """Update playback position for a title.

        Args:
            title_id: Unique title identifier
            position_seconds: Current playback position in seconds
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE watch_history
                SET position_seconds = ?, last_watched_date = CURRENT_TIMESTAMP
                WHERE title_id = ?
                """,
                (position_seconds, title_id),
            )

            conn.commit()

    def delete_watch_record(self, title_id: str) -> None:
        """Delete a watch history record.

        Args:
            title_id: Unique title identifier
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM watch_history WHERE title_id = ?", (title_id,))

            conn.commit()

    def _row_to_watch_history(self, row: sqlite3.Row) -> WatchHistory:
        """Convert database row to WatchHistory object."""
        return WatchHistory(
            id=row["id"],
            title_id=row["title_id"],
            title_name=row["title_name"],
            media_type=MediaType(row["media_type"]),
            title_url=row["title_url"],
            magnet_url=row["magnet_url"],
            last_episode=row["last_episode"],
            last_watched_date=datetime.fromisoformat(row["last_watched_date"]),
            duration_seconds=row["duration_seconds"],
            position_seconds=row["position_seconds"],
        )
