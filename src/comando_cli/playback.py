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
    """Manages torrent streaming and playback via webtorrent-cli with mpv."""

    def __init__(self, config: AppConfig):
        self.config = config
        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        if not shutil.which("mpv"):
            raise PlaybackError("mpv not installed. Install it to enable playback.")
        if not shutil.which("webtorrent"):
            raise PlaybackError("webtorrent-cli not installed. Run: npm install -g webtorrent-cli")

    def play_torrent(
        self,
        magnet_link: str,
        title: Title,
        episode: Optional[int] = None,
    ) -> None:
        display_name = title.name
        if episode:
            display_name = f"{title.name} - Episode {episode}"

        typer.echo(f"🎬 Starting playback: {display_name}")

        try:
            self._stream_with_webtorrent_mpv(magnet_link)
            typer.echo(f"✓ Playback completed: {display_name}")

        except KeyboardInterrupt:
            typer.echo("\n⏹️  Playback interrupted")
        except Exception as e:
            raise PlaybackError(f"Playback failed: {e}") from e

    def _stream_with_webtorrent_mpv(self, magnet_link: str) -> None:
        try:
            result = subprocess.run(["webtorrent", "--mpv", magnet_link], check=False)
            if result.returncode not in (0, 143):
                raise PlaybackError(
                    f"Playback process exited with code {result.returncode}"
                )
        except FileNotFoundError as e:
            raise PlaybackError(f"Failed to start webtorrent: {e}") from e
