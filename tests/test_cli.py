"""Tests for CLI module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

import comando_cli.cli as cli
from comando_cli.cli import app
from comando_cli.models import MediaType, QualityOption, Title, WatchHistory

runner = CliRunner()


class TestSearchCommand:
    """Tests for search command."""

    def test_search_displays_results(self):
        """Test search displays found results."""
        with patch("comando_cli.cli._make_scraper") as mock_scraper_class:
            with patch("comando_cli.cli.ensure_directories"):
                with patch("comando_cli.cli.Database"):
                    mock_scraper = MagicMock()
                    mock_scraper_class.return_value = mock_scraper

                    title1 = Title(
                        id="movie-1",
                        name="Test Movie",
                        media_type=MediaType.MOVIE,
                        url="https://example.com/movie-1",
                    )
                    title2 = Title(
                        id="series-1",
                        name="Test Series",
                        media_type=MediaType.SERIES,
                        url="https://example.com/series-1",
                    )

                    mock_scraper.search.return_value = [title1, title2]

                    result = runner.invoke(app, ["search", "test"])

                    assert result.exit_code == 0
                    assert "Test Movie" in result.stdout
                    assert "Test Series" in result.stdout
                    assert "Found 2 result(s)" in result.stdout

    def test_search_empty_query(self):
        """Test search with empty query shows error."""
        with patch("comando_cli.cli.ensure_directories"):
            with patch("comando_cli.cli.Database"):
                result = runner.invoke(app, ["search", ""])

                assert result.exit_code == 0
                assert (
                    "cannot be empty" in result.stdout
                    or "Search query" in result.stdout
                )

    def test_search_no_results(self):
        """Test search with no results."""
        with patch("comando_cli.cli._make_scraper") as mock_scraper_class:
            with patch("comando_cli.cli.ensure_directories"):
                with patch("comando_cli.cli.Database"):
                    mock_scraper = MagicMock()
                    mock_scraper_class.return_value = mock_scraper
                    mock_scraper.search.return_value = []

                    result = runner.invoke(app, ["search", "nonexistent"])

                    assert result.exit_code == 0
                    assert "No results found" in result.stdout

    def test_search_scraper_error_handling(self):
        """Test search handles scraper errors."""
        with patch("comando_cli.cli._make_scraper") as mock_scraper_class:
            with patch("comando_cli.cli.ensure_directories"):
                with patch("comando_cli.cli.Database"):
                    mock_scraper = MagicMock()
                    mock_scraper_class.return_value = mock_scraper
                    from comando_cli.scraper import ScraperError

                    mock_scraper.search.side_effect = ScraperError("Network error")

                    result = runner.invoke(app, ["search", "test"])

                    assert result.exit_code == 1
                    # Error message may be in output or exception
                    output = result.stdout + (result.stderr or "")
                    assert (
                        "Search error" in output
                        or "Network error" in output
                        or result.exception is not None
                    )


class TestWatchCommand:
    """Tests for watch command."""

    def test_watch_movie_basic_flow(self):
        """Test watching a movie with basic flow."""
        with patch("comando_cli.cli._make_scraper") as mock_scraper_class:
            with patch("comando_cli.cli.select_quality_and_language") as mock_select:
                with patch("comando_cli.cli.TorrentPlayer") as mock_player_class:
                    with patch("comando_cli.cli.ensure_directories"):
                        with patch("comando_cli.cli.Database") as mock_db_class:
                            mock_scraper = MagicMock()
                            mock_scraper_class.return_value = mock_scraper

                            title_search = Title(
                                id="movie-1",
                                name="Test Movie",
                                media_type=MediaType.MOVIE,
                                url="https://example.com/movie-1",
                            )

                            title_detail = Title(
                                id="movie-1",
                                name="Test Movie",
                                media_type=MediaType.MOVIE,
                                url="https://example.com/movie-1",
                                quality_options=[
                                    QualityOption(
                                        quality="1080p",
                                        language="Portuguese",
                                        magnet_link="magnet:?xt=urn:btih:test",
                                    )
                                ],
                            )

                            mock_scraper.search.return_value = [title_search]
                            mock_scraper.fetch_metadata.return_value = title_detail

                            quality_option = QualityOption(
                                quality="1080p",
                                language="Portuguese",
                                magnet_link="magnet:?xt=urn:btih:test",
                            )
                            mock_select.return_value = quality_option

                            mock_db = MagicMock()
                            mock_db_class.return_value = mock_db

                            mock_player = MagicMock()
                            mock_player_class.return_value = mock_player

                            result = runner.invoke(app, ["watch", "test"])

                            assert result.exit_code == 0
                            assert "Selected: Test Movie" in result.stdout
                            mock_player.play_torrent.assert_called_once()

    def test_watch_series_with_episodes(self):
        """Test watching a series with episode selection."""
        with patch("comando_cli.cli._make_scraper") as mock_scraper_class:
            with patch("comando_cli.cli.select_quality_and_language") as mock_select:
                with patch("comando_cli.cli.parse_episode_syntax") as mock_parse:
                    with patch("comando_cli.cli.TorrentPlayer") as mock_player_class:
                        with patch("comando_cli.cli.ensure_directories"):
                            with patch("comando_cli.cli.Database") as mock_db_class:
                                mock_scraper = MagicMock()
                                mock_scraper_class.return_value = mock_scraper

                                from comando_cli.episode_selector import EpisodeRange

                                title_search = Title(
                                    id="series-1",
                                    name="Test Series",
                                    media_type=MediaType.SERIES,
                                    url="https://example.com/series-1",
                                )

                                title_detail = Title(
                                    id="series-1",
                                    name="Test Series",
                                    media_type=MediaType.SERIES,
                                    url="https://example.com/series-1",
                                    quality_options=[
                                        QualityOption(
                                            quality="1080p",
                                            language="Portuguese",
                                            magnet_link="magnet:?xt=urn:btih:test",
                                        )
                                    ],
                                    episodes=[],  # Add episodes if needed
                                )

                                mock_scraper.search.return_value = [title_search]
                                mock_scraper.fetch_metadata.return_value = title_detail

                                mock_parse.return_value = EpisodeRange(
                                    episodes=[1, 2, 3],
                                    original_input="1-3",
                                )

                                quality_option = QualityOption(
                                    quality="1080p",
                                    language="Portuguese",
                                    magnet_link="magnet:?xt=urn:btih:test",
                                )
                                mock_select.return_value = quality_option

                                mock_db = MagicMock()
                                mock_db_class.return_value = mock_db

                                mock_player = MagicMock()
                                mock_player_class.return_value = mock_player

                                result = runner.invoke(
                                    app, ["watch", "series", "-e", "1-3"]
                                )

                                assert result.exit_code == 0
                                assert "Episodes:" in result.stdout

    def test_watch_no_results(self):
        """Test watch when search returns no results."""
        with patch("comando_cli.cli._make_scraper") as mock_scraper_class:
            with patch("comando_cli.cli.ensure_directories"):
                with patch("comando_cli.cli.Database"):
                    mock_scraper = MagicMock()
                    mock_scraper_class.return_value = mock_scraper
                    mock_scraper.search.return_value = []

                    result = runner.invoke(app, ["watch", "nonexistent"])

                    assert result.exit_code == 0
                    assert "No results found" in result.stdout

    def test_watch_no_quality_selected(self):
        """Test watch when user doesn't select a quality."""
        with patch("comando_cli.cli._make_scraper") as mock_scraper_class:
            with patch("comando_cli.cli.select_quality_and_language") as mock_select:
                with patch("comando_cli.cli.ensure_directories"):
                    with patch("comando_cli.cli.Database"):
                        mock_scraper = MagicMock()
                        mock_scraper_class.return_value = mock_scraper

                        title_search = Title(
                            id="movie-1",
                            name="Test Movie",
                            media_type=MediaType.MOVIE,
                            url="https://example.com/movie-1",
                        )

                        title_detail = Title(
                            id="movie-1",
                            name="Test Movie",
                            media_type=MediaType.MOVIE,
                            url="https://example.com/movie-1",
                            quality_options=[],
                        )

                        mock_scraper.search.return_value = [title_search]
                        mock_scraper.fetch_metadata.return_value = title_detail
                        mock_select.return_value = None  # User cancelled

                        result = runner.invoke(app, ["watch", "test"])

                        assert result.exit_code == 0
                        assert "No quality selected" in result.stdout

    def test_watch_return_to_search_restarts_flow(self):
        """Test watch loops back to search when playback requests it."""
        with patch("comando_cli.cli._make_scraper") as mock_scraper_class:
            with patch("comando_cli.cli.select_title") as mock_select_title:
                with patch("comando_cli.cli._play_title") as mock_play_title:
                    mock_scraper = MagicMock()
                    mock_scraper_class.return_value = mock_scraper

                    title = Title(
                        id="series-1",
                        name="Test Series",
                        media_type=MediaType.SERIES,
                        url="https://example.com/series-1",
                    )
                    detail = Title(
                        id="series-1",
                        name="Test Series",
                        media_type=MediaType.SERIES,
                        url="https://example.com/series-1",
                        quality_options=[],
                    )

                    mock_scraper.search.return_value = [title]
                    mock_scraper.fetch_metadata.return_value = detail
                    mock_select_title.return_value = title
                    mock_play_title.side_effect = [True, False]

                    result = runner.invoke(app, ["watch", "series"])

                    assert result.exit_code == 0
                    assert "Returning to search" in result.stdout
                    assert mock_scraper.search.call_count == 2
                    assert mock_play_title.call_count == 2


class TestPostPlaybackMenu:
    """Tests for post-playback actions."""

    def test_select_post_playback_action_with_fzf(self):
        """Test selecting action from fzf output."""
        with patch("comando_cli.cli.select_with_fzf", return_value="Próximo"):

            action = cli._select_post_playback_action()

            assert action == "proximo"

    def test_select_post_playback_action_fallback_prompt(self):
        """Test fallback numeric menu when fzf is unavailable."""
        with patch("comando_cli.cli.select_with_fzf", return_value=None):
            with patch("typer.prompt", return_value=2):
                action = cli._select_post_playback_action()

                assert action == "anterior"


class TestHistoryCommand:
    """Tests for history command."""

    def test_history_shows_watch_records(self):
        """Test history displays watch records."""
        mock_db = MagicMock()

        record1 = WatchHistory(
            id=1,
            title_id="movie-1",
            title_name="Test Movie",
            media_type=MediaType.MOVIE,
            last_episode=None,
            last_watched_date=datetime(2026, 2, 23, 10, 0),
            duration_seconds=7200,
            position_seconds=0,
        )

        record2 = WatchHistory(
            id=2,
            title_id="series-1",
            title_name="Test Series",
            media_type=MediaType.SERIES,
            last_episode=5,
            last_watched_date=datetime(2026, 2, 23, 15, 30),
            duration_seconds=0,
            position_seconds=0,
        )

        mock_db.get_all_watch_history.return_value = [record1, record2]

        with patch("comando_cli.cli.db", mock_db):
            result = runner.invoke(app, ["history"])

        assert result.exit_code == 0
        assert "Test Movie" in result.stdout
        assert "Test Series" in result.stdout
        assert "Ep. 5" in result.stdout

    def test_history_empty(self):
        """Test history shows message when empty."""
        mock_db = MagicMock()
        mock_db.get_all_watch_history.return_value = []

        with patch("comando_cli.cli.db", mock_db):
            result = runner.invoke(app, ["history"])

        assert result.exit_code == 0
        assert "No watch history" in result.stdout


class TestResumeCommand:
    """Tests for resume command."""

    def test_resume_shows_last_watched(self):
        """Test resume displays last watched title."""
        mock_db = MagicMock()

        last_watch = WatchHistory(
            id=1,
            title_id="series-1",
            title_name="Test Series",
            media_type=MediaType.SERIES,
            last_episode=5,
            last_watched_date=datetime(2026, 2, 23, 15, 30),
            duration_seconds=0,
            position_seconds=0,
        )

        mock_db.get_last_watched.return_value = last_watch

        with patch("comando_cli.cli.db", mock_db):
            result = runner.invoke(app, ["resume"])

        assert result.exit_code == 0
        assert "Resuming: Test Series" in result.stdout

    def test_resume_empty_history(self):
        """Test resume shows message when no history."""
        mock_db = MagicMock()
        mock_db.get_last_watched.return_value = None

        with patch("comando_cli.cli.db", mock_db):
            result = runner.invoke(app, ["resume"])

        assert result.exit_code == 0
        assert "No watch history to resume" in result.stdout


class TestAppInitialization:
    """Tests for app initialization."""

    def test_app_has_commands(self):
        """Test app has all required commands."""
        # Check that app has the expected commands
        _ = {cmd.name for cmd in app.registered_commands}

        # Typer app structure is different, check by invoking help
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "search" in result.stdout
        assert "update" in result.stdout
        assert "watch" in result.stdout
        assert "history" in result.stdout
        assert "resume" in result.stdout

    def test_app_help_shows_description(self):
        """Test app help shows description."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Comando CLI" in result.stdout or "Stream" in result.stdout

    def test_global_comando_flag_forces_comando_la_scraper(self):
        """Test --comando global flag overrides configured scraper."""
        with patch("comando_cli.cli.GratistorrentScraper") as mock_gt_class:
            with patch("comando_cli.cli.ComandoLaScraper") as mock_comando_class:
                mock_scraper = MagicMock()
                mock_scraper.search.return_value = []
                mock_comando_class.return_value = mock_scraper

                result = runner.invoke(app, ["--comando", "search", "test"])

                assert result.exit_code == 0
                mock_comando_class.assert_called_once()
                mock_gt_class.assert_not_called()


class TestVersionAndUpdate:
    """Tests for version and update CLI flows."""

    def test_version_flag(self):
        """Test global --version shows current package version."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "comando-cli" in result.stdout
        assert cli.__version__ in result.stdout

    def test_update_check_when_up_to_date(self):
        """Test update --check reports latest when no update exists."""
        with patch("comando_cli.cli._fetch_remote_version", return_value=cli.__version__):
            result = runner.invoke(app, ["update", "--check"])

        assert result.exit_code == 0
        assert "Current version" in result.stdout
        assert "Remote version" in result.stdout
        assert "latest version" in result.stdout

    def test_update_check_when_update_available(self):
        """Test update --check reports availability without installing."""
        with patch("comando_cli.cli._fetch_remote_version", return_value="999.0.0"):
            with patch("comando_cli.cli._run_remote_installer") as mock_install:
                result = runner.invoke(app, ["update", "--check"])

        assert result.exit_code == 0
        assert "Update available" in result.stdout
        mock_install.assert_not_called()

    def test_update_runs_installer_with_yes(self):
        """Test update installs when newer version exists and -y is provided."""
        with patch("comando_cli.cli._fetch_remote_version", return_value="999.0.0"):
            with patch("comando_cli.cli._run_remote_installer") as mock_install:
                result = runner.invoke(app, ["update", "-y"])

        assert result.exit_code == 0
        assert "Installing update" in result.stdout
        assert "Update finished" in result.stdout
        mock_install.assert_called_once()

    def test_fetch_remote_version_prefers_latest_semver_tag(self):
        """Test remote version lookup picks highest semantic tag from GitHub tags."""
        mock_tags = [
            {"name": "v0.1.1"},
            {"name": "v0.1.9"},
            {"name": "v0.1.10"},
            {"name": "docs"},
        ]
        tags_response = MagicMock()
        tags_response.json.return_value = mock_tags
        tags_response.raise_for_status.return_value = None

        pyproject_response = MagicMock()
        pyproject_response.raise_for_status.return_value = None
        pyproject_response.text = '[project]\nversion = "0.1.0"\n'

        with patch(
            "comando_cli.cli.requests.get",
            side_effect=[tags_response, pyproject_response],
        ):
            remote_version = cli._fetch_remote_version()

        assert remote_version == "0.1.10"

    def test_fetch_remote_version_falls_back_to_pyproject(self):
        """Test remote version lookup falls back to pyproject when tag lookup fails."""
        tags_error = cli.requests.RequestException("tags unavailable")
        pyproject_response = MagicMock()
        pyproject_response.raise_for_status.return_value = None
        pyproject_response.text = '[project]\nversion = "0.2.0"\n'

        with patch("comando_cli.cli.requests.get", side_effect=[tags_error, pyproject_response]):
            remote_version = cli._fetch_remote_version()

        assert remote_version == "0.2.0"

    def test_fetch_remote_version_uses_highest_between_tags_and_pyproject(self):
        """Test remote version lookup picks higher version between tags and pyproject."""
        tags_response = MagicMock()
        tags_response.raise_for_status.return_value = None
        tags_response.json.return_value = [{"name": "v0.2.0"}]

        pyproject_response = MagicMock()
        pyproject_response.raise_for_status.return_value = None
        pyproject_response.text = '[project]\nversion = "0.2.1"\n'

        with patch("comando_cli.cli.requests.get", side_effect=[tags_response, pyproject_response]):
            remote_version = cli._fetch_remote_version()

        assert remote_version == "0.2.1"
