"""Torrent streaming and playback management."""

import shutil
import subprocess
from typing import Optional

import typer

from .config import AppConfig
from .models import Title


class PlaybackError(Exception):
    """Playback-related error."""

    pass


class TorrentPlayer:
    """Manages torrent streaming and playback via webtorrent-cli + mpv."""

    def __init__(self, config: AppConfig):
        """Initialize player.

        Args:
            config: AppConfig instance

        Raises:
            PlaybackError: If required dependencies are not installed
        """
        self.config = config
        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        """Validate required external dependencies.

        Raises:
            PlaybackError: If mpv or webtorrent-cli not found
        """
        if not shutil.which("mpv"):
            raise PlaybackError("mpv not installed. Install it to enable playback.")

        if not shutil.which("webtorrent"):
            raise PlaybackError(
                "webtorrent-cli not installed. Install with: npm install -g webtorrent-cli"
            )

    def play_torrent(
        self,
        magnet_link: str,
        title: Title,
        episode: Optional[int] = None,
    ) -> None:
        """Stream and play a torrent using webtorrent + mpv.

        Args:
            magnet_link: Magnet link to stream
            title: Title information for reference
            episode: Episode number (for series)

        Raises:
            PlaybackError: If playback fails
        """
        display_name = title.name
        if episode:
            display_name = f"{title.name} - Episode {episode}"

        typer.echo(f"🎬 Starting playback: {display_name}")

        try:
            # Stream torrent directly with webtorrent --mpv
            self._stream_with_webtorrent_mpv(magnet_link)
            typer.echo(f"✓ Playback completed: {display_name}")

        except KeyboardInterrupt:
            typer.echo("\n⏹️  Playback interrupted")
        except Exception as e:
            raise PlaybackError(f"Playback failed: {e}") from e

    def _stream_with_webtorrent_mpv(self, magnet_link: str) -> None:
        """Stream torrent directly with webtorrent --mpv.

        Args:
            magnet_link: Magnet link to stream

        Raises:
            PlaybackError: If process fails
        """
        cmd = ["webtorrent", "--mpv", magnet_link]

        try:
            result = subprocess.run(cmd, check=False)
            if result.returncode not in (0, 143):  # 143 is SIGTERM (user interrupt)
                raise PlaybackError(f"Playback process exited with code {result.returncode}")

        except FileNotFoundError as e:
            raise PlaybackError(f"Failed to start webtorrent: {e}") from e
