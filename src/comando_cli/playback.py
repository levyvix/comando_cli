"""Torrent streaming and playback management."""

import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

import typer

from .config import AppConfig
from .models import Title


class PlaybackError(Exception):
    """Playback-related error."""

    pass


class TorrentPlayer:
    """Manages torrent download and playback via mpv."""

    def __init__(self, config: AppConfig):
        """Initialize player.

        Args:
            config: AppConfig instance
        """
        self.config = config
        self.cache_dir = config.cache_dir / "torrents"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        """Validate required external dependencies."""
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
        """Stream and play a torrent.

        Args:
            magnet_link: Magnet link or torrent URL
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
            # Start webtorrent download
            process = self._start_webtorrent_download(magnet_link)

            # Wait for file to be available
            torrent_file = self._wait_for_torrent_file(process)

            # Launch mpv
            self._launch_mpv(torrent_file)

            # Cleanup
            self._cleanup(process)

            typer.echo(f"✓ Playback completed: {display_name}")

        except KeyboardInterrupt:
            typer.echo("\n⏹️  Playback interrupted")
            self._cleanup(process)
        except Exception as e:
            raise PlaybackError(f"Playback failed: {e}") from e

    def _start_webtorrent_download(self, magnet_link: str) -> subprocess.Popen:
        """Start webtorrent download process.

        Args:
            magnet_link: Magnet link

        Returns:
            Popen process object
        """
        cmd = [
            "webtorrent",
            magnet_link,
            "--output",
            str(self.cache_dir),
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return process
        except FileNotFoundError as e:
            raise PlaybackError(f"Failed to start webtorrent: {e}") from e

    def _wait_for_torrent_file(
        self,
        process: subprocess.Popen,
        timeout: int = 300,
        check_interval: int = 2,
    ) -> Path:
        """Wait for torrent file to become available for playback.

        Args:
            process: Webtorrent process
            timeout: Maximum time to wait in seconds
            check_interval: How often to check for file in seconds

        Returns:
            Path to playable file

        Raises:
            PlaybackError: If timeout or file not found
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check if process is still running
            if process.poll() is not None:
                raise PlaybackError("Webtorrent process exited unexpectedly")

            # List files in cache directory
            files = list(self.cache_dir.glob("*"))
            media_files = [f for f in files if f.suffix.lower() in (".mkv", ".mp4", ".avi")]

            if media_files:
                # Return the largest file (usually the complete one)
                largest_file = max(media_files, key=lambda f: f.stat().st_size)
                return largest_file

            time.sleep(check_interval)

        raise PlaybackError(f"Timeout waiting for torrent file (>{timeout}s)")

    def _launch_mpv(self, file_path: Path) -> None:
        """Launch mpv player.

        Args:
            file_path: Path to file to play
        """
        cmd = ["mpv", str(file_path)]

        try:
            subprocess.run(cmd, check=False)  # mpv handles user interruption
        except FileNotFoundError as e:
            raise PlaybackError(f"Failed to launch mpv: {e}") from e

    def _cleanup(self, process: Optional[subprocess.Popen] = None) -> None:
        """Cleanup webtorrent process and cache.

        Args:
            process: Webtorrent process to terminate
        """
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

        # Clean up old cache files if needed
        if self.config.cache_dir.exists():
            total_size = sum(
                f.stat().st_size for f in self.config.cache_dir.rglob("*") if f.is_file()
            )
            max_size_bytes = self.config.max_concurrent_downloads * 1024 * 1024 * 1024

            if total_size > max_size_bytes:
                self._cleanup_old_files()

    def _cleanup_old_files(self) -> None:
        """Clean up oldest files in cache when size limit exceeded."""
        files = sorted(
            (f for f in self.config.cache_dir.rglob("*") if f.is_file()),
            key=lambda f: f.stat().st_mtime,
        )

        for file_path in files[:5]:  # Remove 5 oldest files
            try:
                file_path.unlink()
            except OSError:
                pass
