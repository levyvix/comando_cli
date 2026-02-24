"""Tests for database module."""

import tempfile
from pathlib import Path

import pytest

from comando_cli.db import Database
from comando_cli.models import MediaType


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)
        yield db


class TestDatabase:
    """Tests for Database class."""

    def test_database_initialization(self, temp_db):
        """Test database is initialized correctly."""
        assert temp_db.db_path.exists()

    def test_add_watch_record_movie(self, temp_db):
        """Test adding watch record for a movie."""
        record = temp_db.add_watch_record(
            title_id="movie-1",
            title_name="Test Movie",
            media_type=MediaType.MOVIE,
            duration_seconds=7200,
        )

        assert record.title_id == "movie-1"
        assert record.title_name == "Test Movie"
        assert record.media_type == MediaType.MOVIE
        assert record.duration_seconds == 7200

    def test_add_watch_record_series(self, temp_db):
        """Test adding watch record for a series."""
        record = temp_db.add_watch_record(
            title_id="series-1",
            title_name="Test Series",
            media_type=MediaType.SERIES,
            last_episode=5,
        )

        assert record.title_id == "series-1"
        assert record.media_type == MediaType.SERIES
        assert record.last_episode == 5

    def test_get_watch_record(self, temp_db):
        """Test retrieving watch record."""
        temp_db.add_watch_record(
            title_id="movie-1",
            title_name="Test Movie",
            media_type=MediaType.MOVIE,
        )

        record = temp_db.get_watch_record("movie-1")

        assert record is not None
        assert record.title_id == "movie-1"
        assert record.title_name == "Test Movie"

    def test_get_watch_record_not_found(self, temp_db):
        """Test retrieving non-existent watch record."""
        record = temp_db.get_watch_record("non-existent")

        assert record is None

    def test_get_all_watch_history(self, temp_db):
        """Test retrieving all watch history."""
        temp_db.add_watch_record(
            title_id="movie-1",
            title_name="Movie 1",
            media_type=MediaType.MOVIE,
        )
        temp_db.add_watch_record(
            title_id="series-1",
            title_name="Series 1",
            media_type=MediaType.SERIES,
        )

        records = temp_db.get_all_watch_history()

        assert len(records) == 2
        assert any(r.title_id == "movie-1" for r in records)
        assert any(r.title_id == "series-1" for r in records)

    def test_get_all_watch_history_empty(self, temp_db):
        """Test retrieving empty watch history."""
        records = temp_db.get_all_watch_history()

        assert records == []

    def test_get_last_watched(self, temp_db):
        """Test retrieving last watched title."""
        temp_db.add_watch_record(
            title_id="movie-1",
            title_name="Movie 1",
            media_type=MediaType.MOVIE,
        )
        temp_db.add_watch_record(
            title_id="movie-2",
            title_name="Movie 2",
            media_type=MediaType.MOVIE,
        )

        last = temp_db.get_last_watched()

        assert last is not None
        assert last.title_id == "movie-2"

    def test_get_last_watched_empty(self, temp_db):
        """Test retrieving last watched from empty history."""
        last = temp_db.get_last_watched()

        assert last is None

    def test_update_position(self, temp_db):
        """Test updating playback position."""
        temp_db.add_watch_record(
            title_id="movie-1",
            title_name="Test Movie",
            media_type=MediaType.MOVIE,
        )

        temp_db.update_position("movie-1", 1800)

        record = temp_db.get_watch_record("movie-1")
        assert record.position_seconds == 1800

    def test_delete_watch_record(self, temp_db):
        """Test deleting watch record."""
        temp_db.add_watch_record(
            title_id="movie-1",
            title_name="Test Movie",
            media_type=MediaType.MOVIE,
        )

        temp_db.delete_watch_record("movie-1")

        record = temp_db.get_watch_record("movie-1")
        assert record is None

    def test_update_existing_record(self, temp_db):
        """Test updating existing record."""
        first = temp_db.add_watch_record(
            title_id="movie-1",
            title_name="Movie 1",
            media_type=MediaType.MOVIE,
            last_episode=1,
        )

        second = temp_db.add_watch_record(
            title_id="movie-1",
            title_name="Movie 1 Updated",
            media_type=MediaType.MOVIE,
            last_episode=2,
        )

        # Should be same ID (UNIQUE constraint)
        assert first.id == second.id

        # Should have updated values
        record = temp_db.get_watch_record("movie-1")
        assert record.last_episode == 2

    def test_watch_history_ordering(self, temp_db):
        """Test watch history is ordered by last watched date."""
        temp_db.add_watch_record(
            title_id="movie-1",
            title_name="Movie 1",
            media_type=MediaType.MOVIE,
        )

        # Small delay and add another
        import time
        time.sleep(0.01)

        temp_db.add_watch_record(
            title_id="movie-2",
            title_name="Movie 2",
            media_type=MediaType.MOVIE,
        )

        records = temp_db.get_all_watch_history()

        # Most recent should be first
        assert records[0].title_id == "movie-2"
        assert records[1].title_id == "movie-1"
