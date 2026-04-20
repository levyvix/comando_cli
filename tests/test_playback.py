"""Tests for playback module."""

from unittest.mock import MagicMock, patch

import pytest

from comando_cli.models import MediaType, Title
from comando_cli.playback import PlaybackError, TorrentPlayer


@pytest.fixture
def sample_title():
    """Create a sample title for testing."""
    return Title(
        id="test-movie",
        name="Test Movie",
        media_type=MediaType.MOVIE,
        url="https://example.com/test",
    )


@pytest.fixture
def sample_series():
    """Create a sample series for testing."""
    return Title(
        id="test-series",
        name="Test Series",
        media_type=MediaType.SERIES,
        url="https://example.com/test-series",
    )


class TestTorrentPlayerInit:
    """Tests for TorrentPlayer initialization."""

    def test_init_with_valid_dependencies(self):
        """Test initialization with required dependencies available."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/command"
            from comando_cli.config import AppConfig

            config = AppConfig()
            player = TorrentPlayer(config)

            assert player.config == config

    def test_init_missing_mpv_raises_error(self):
        """Test initialization fails when mpv is not installed."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: "/usr/bin/webtorrent" if cmd == "webtorrent" else None

            from comando_cli.config import AppConfig

            config = AppConfig()

            with pytest.raises(PlaybackError, match="mpv"):
                TorrentPlayer(config)

    def test_init_missing_webtorrent_raises_error(self):
        """Test initialization fails when webtorrent-cli is not installed."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: "/usr/bin/mpv" if cmd == "mpv" else None

            from comando_cli.config import AppConfig

            config = AppConfig()

            with pytest.raises(PlaybackError, match="webtorrent-cli"):
                TorrentPlayer(config)


class TestPlayTorrent:
    """Tests for play_torrent method."""

    def test_play_torrent_movie(self, sample_title):
        """Test playing a movie torrent."""
        with patch("shutil.which", return_value="/usr/bin/command"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                from comando_cli.config import AppConfig

                config = AppConfig()
                player = TorrentPlayer(config)

                magnet = "magnet:?xt=urn:btih:test"
                player.play_torrent(magnet, sample_title)

                # Verify webtorrent was called with correct arguments
                mock_run.assert_called_once()
                call_args = mock_run.call_args[0][0]
                assert call_args[0] == "webtorrent"
                assert call_args[1] == "--mpv"
                assert "--out" in call_args
                assert call_args[-1] == magnet

    def test_play_torrent_series_with_episode(self, sample_series):
        """Test playing a series episode."""
        with patch("shutil.which", return_value="/usr/bin/command"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                from comando_cli.config import AppConfig

                config = AppConfig()
                player = TorrentPlayer(config)

                magnet = "magnet:?xt=urn:btih:test"
                player.play_torrent(magnet, sample_series, episode=5)

                # Verify call was made
                mock_run.assert_called_once()

    def test_play_torrent_keyboard_interrupt(self, sample_title):
        """Test graceful handling of user interrupt."""
        with patch("shutil.which", return_value="/usr/bin/command"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = KeyboardInterrupt()
                from comando_cli.config import AppConfig

                config = AppConfig()
                player = TorrentPlayer(config)

                # Should not raise, just handle gracefully
                magnet = "magnet:?xt=urn:btih:test"
                player.play_torrent(magnet, sample_title)

                mock_run.assert_called_once()

    def test_play_torrent_process_failure(self, sample_title):
        """Test error handling when webtorrent exits with error code."""
        with patch("shutil.which", return_value="/usr/bin/command"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1)
                from comando_cli.config import AppConfig

                config = AppConfig()
                player = TorrentPlayer(config)

                magnet = "magnet:?xt=urn:btih:test"

                with pytest.raises(PlaybackError, match="Playback process exited with code"):
                    player.play_torrent(magnet, sample_title)

    def test_play_torrent_sigterm_handled_gracefully(self, sample_title):
        """Test that SIGTERM exit code (143) is handled as normal completion."""
        with patch("shutil.which", return_value="/usr/bin/command"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=143)
                from comando_cli.config import AppConfig

                config = AppConfig()
                player = TorrentPlayer(config)

                magnet = "magnet:?xt=urn:btih:test"
                # Should not raise
                player.play_torrent(magnet, sample_title)

                mock_run.assert_called_once()

    def test_play_torrent_command_not_found(self, sample_title):
        """Test error when webtorrent command is not found."""
        with patch("shutil.which", return_value="/usr/bin/command"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = FileNotFoundError("webtorrent not found")
                from comando_cli.config import AppConfig

                config = AppConfig()
                player = TorrentPlayer(config)

                magnet = "magnet:?xt=urn:btih:test"

                with pytest.raises(PlaybackError, match="Failed to start webtorrent"):
                    player.play_torrent(magnet, sample_title)


class TestStreamWithWebtorrentMpv:
    """Tests for _stream_with_webtorrent_mpv method."""

    def test_stream_success(self, sample_title):
        """Test successful streaming."""
        with patch("shutil.which", return_value="/usr/bin/command"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                from comando_cli.config import AppConfig

                config = AppConfig()
                player = TorrentPlayer(config)

                magnet = "magnet:?xt=urn:btih:test123"
                player._stream_with_webtorrent_mpv(magnet)

                mock_run.assert_called_once()
                call_args = mock_run.call_args[0][0]
                assert call_args[0] == "webtorrent"
                assert call_args[1] == "--mpv"
                assert "--out" in call_args
                assert call_args[-1] == magnet

    def test_stream_exit_code_zero(self, sample_title):
        """Test exit code 0 is successful."""
        with patch("shutil.which", return_value="/usr/bin/command"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                from comando_cli.config import AppConfig

                config = AppConfig()
                player = TorrentPlayer(config)

                # Should not raise
                player._stream_with_webtorrent_mpv("magnet:?xt=urn:btih:test")

    def test_stream_exit_code_143_accepted(self, sample_title):
        """Test exit code 143 (SIGTERM) is accepted."""
        with patch("shutil.which", return_value="/usr/bin/command"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=143)
                from comando_cli.config import AppConfig

                config = AppConfig()
                player = TorrentPlayer(config)

                # Should not raise
                player._stream_with_webtorrent_mpv("magnet:?xt=urn:btih:test")

    def test_stream_invalid_exit_code_raises_error(self, sample_title):
        """Test non-zero, non-143 exit codes raise error."""
        with patch("shutil.which", return_value="/usr/bin/command"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=2)
                from comando_cli.config import AppConfig

                config = AppConfig()
                player = TorrentPlayer(config)

                with pytest.raises(PlaybackError, match="Playback process exited with code 2"):
                    player._stream_with_webtorrent_mpv("magnet:?xt=urn:btih:test")

    def test_stream_file_not_found_raises_error(self, sample_title):
        """Test FileNotFoundError is wrapped in PlaybackError."""
        with patch("shutil.which", return_value="/usr/bin/command"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = FileNotFoundError("Command not found")
                from comando_cli.config import AppConfig

                config = AppConfig()
                player = TorrentPlayer(config)

                with pytest.raises(PlaybackError, match="Failed to start webtorrent"):
                    player._stream_with_webtorrent_mpv("magnet:?xt=urn:btih:test")
