"""Torrent streaming and playback management."""

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import typer

from comando_cli.config import AppConfig
from comando_cli.models import Title, TorrentFile

_VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".mov", ".m4v", ".wmv", ".flv", ".webm"}

_EP_PATTERNS = [
    re.compile(r"[Ss]\d{1,2}[Ee](\d{1,2})"),  # S01E03
    re.compile(r"[Ee][Pp]?\.?\s*(\d{1,3})"),  # EP03, Ep.3, E03
    re.compile(r"(?<!\d)(\d{1,3})(?!\d)"),  # bare number fallback
]


def _extract_episode_from_path(path: str) -> Optional[int]:
    """Extract episode number from a filename/path."""
    filename = path.split("/")[-1]
    for pattern in _EP_PATTERNS:
        m = pattern.search(filename)
        if m:
            return int(m.group(1))
    return None


def _is_video_file(path: str) -> bool:
    return any(path.lower().endswith(ext) for ext in _VIDEO_EXTENSIONS)


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
            raise PlaybackError("`mpv` not installed. Install it to enable playback.")
        if not shutil.which("webtorrent"):
            raise PlaybackError(
                "`webtorrent-cli` not installed. Run: npm install -g webtorrent-cli"
            )

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

    def list_torrent_files(self, magnet_link: str) -> list[TorrentFile]:
        """List files in a torrent by resolving metadata from DHT/trackers.

        Uses a Node.js script with the webtorrent package (bundled inside
        webtorrent-cli) so it actually connects to peers. May take ~30-60s.
        """
        typer.echo("🔍 Resolving torrent metadata (this may take a moment)...")

        wt_bin = shutil.which("webtorrent")
        if not wt_bin:
            raise PlaybackError("webtorrent not found in PATH")

        # webtorrent binary is a symlink to webtorrent-cli/bin/cmd.js;
        # resolve to the real path to find the bundled node_modules.
        wt_real = Path(wt_bin).resolve()
        cli_nm = wt_real.parent.parent / "node_modules"

        wt_pkg = cli_nm / "webtorrent" / "index.js"
        mem_pkg = cli_nm / "memory-chunk-store" / "index.js"

        if not wt_pkg.exists() or not mem_pkg.exists():
            raise PlaybackError(
                f"Cannot find webtorrent/memory-chunk-store under {cli_nm}"
            )

        script = f"""
import WebTorrent from {json.dumps(str(wt_pkg))};
import MemStore from {json.dumps(str(mem_pkg))};
const client = new WebTorrent();
client.add(process.argv[2], {{ store: MemStore }}, torrent => {{
  const files = torrent.files.map((f, i) => ({{
    index: i, name: f.name, path: f.path, length: f.length
  }}));
  process.stdout.write(JSON.stringify(files) + '\\n');
  client.destroy(() => process.exit(0));
}});
setTimeout(() => {{ process.stderr.write('timeout\\n'); process.exit(1); }}, 90000);
"""
        with tempfile.NamedTemporaryFile(suffix=".mjs", mode="w", delete=False) as tmp:
            tmp.write(script)
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                ["node", tmp_path, magnet_link],
                capture_output=True,
                text=True,
                timeout=100,
            )
        except subprocess.TimeoutExpired:
            raise PlaybackError("Timed out resolving torrent metadata")
        except FileNotFoundError as e:
            raise PlaybackError(f"node not found: {e}") from e
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        if result.returncode != 0 or not result.stdout.strip():
            raise PlaybackError(
                f"Metadata resolution failed: {result.stderr.strip() or 'no output'}"
            )

        try:
            raw_files = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise PlaybackError(f"Failed to parse torrent file list: {e}") from e

        files: list[TorrentFile] = []
        for f in raw_files:
            path = f.get("path") or f.get("name", "")
            length = f.get("length", 0)
            index = f.get("index", 0)
            episode = _extract_episode_from_path(path)
            files.append(
                TorrentFile(index=index, path=path, length=length, episode=episode)
            )

        return files

    def play_torrent_playlist(
        self,
        magnet_link: str,
        start_index: int,
        title: Title,
        start_episode: Optional[int] = None,
    ) -> None:
        """Stream a consolidated torrent as a playlist starting from a specific file.

        Uses --playlist so mpv receives all torrent files as a playlist and
        handles next/prev episode navigation natively. --select sets the
        starting position.
        """
        display_name = title.name
        if start_episode is not None:
            display_name = f"{title.name} from Episode {start_episode}"

        typer.echo(f"🎬 Starting playback: {display_name}")
        typer.echo("   (use > / ] in mpv to go to next episode)")
        with tempfile.TemporaryDirectory(prefix="webtorrent_") as tmp_dir:
            try:
                result = subprocess.run(
                    [
                        "webtorrent",
                        magnet_link,
                        "--mpv",
                        "--playlist",
                        "--select",
                        str(start_index),
                        "--out",
                        tmp_dir,
                    ],
                    check=False,
                )
                if result.returncode not in (0, 143):
                    raise PlaybackError(
                        f"Playback process exited with code {result.returncode}"
                    )
                typer.echo(f"✓ Playback ended: {title.name}")
            except KeyboardInterrupt:
                typer.echo("\n⏹️  Playback interrupted")
            except FileNotFoundError as e:
                raise PlaybackError(f"Failed to start webtorrent: {e}") from e

    def _stream_with_webtorrent_mpv(self, magnet_link: str) -> None:
        with tempfile.TemporaryDirectory(prefix="webtorrent_") as tmp_dir:
            try:
                result = subprocess.run(
                    [
                        "webtorrent",
                        "--mpv",
                        "--playlist",
                        "--out",
                        tmp_dir,
                        magnet_link,
                    ],
                    check=False,
                )
                if result.returncode not in (0, 143):
                    raise PlaybackError(
                        f"Playback process exited with code {result.returncode}"
                    )
            except FileNotFoundError as e:
                raise PlaybackError(f"Failed to start webtorrent: {e}") from e
