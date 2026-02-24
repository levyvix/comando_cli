"""Torrent streaming and playback management."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional

import typer

from .config import AppConfig
from .models import Title


class PlaybackError(Exception):
    """Playback-related error."""

    pass


class TorrentPlayer:
    """Manages torrent streaming and playback via mpv with mpv-webtorrent-hook."""

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
        """Validate required external dependencies, installing what's missing.

        Raises:
            PlaybackError: If mpv not found or hook installation fails
        """
        if not shutil.which("mpv"):
            raise PlaybackError("mpv not installed. Install it to enable playback.")

        self._ensure_webtorrent_hook()

    def _ensure_webtorrent_hook(self) -> None:
        """Ensure mpv-webtorrent-hook and its dependencies are installed and configured.

        On first run (or if setup is incomplete):
        - Installs webtorrent-cli (via npm)
        - Installs jq and xidel (via system package manager)
        - Clones mpv-webtorrent-hook into ~/.config/mpv/scripts/
        - Patches webtorrent-wrap.sh with the full webtorrent binary path
          so mpv can find it regardless of the shell PATH

        Raises:
            PlaybackError: If installation fails
        """
        hook_dir = Path.home() / ".config" / "mpv" / "scripts" / "webtorrent-hook"
        wrap_sh = hook_dir / "webtorrent-wrap.sh"

        self._install_system_deps(["jq", "xidel"])
        self._install_webtorrent_cli()

        if not hook_dir.exists():
            typer.echo("mpv-webtorrent-hook não encontrado. Instalando...")
            self._clone_hook(hook_dir)
            typer.echo("mpv-webtorrent-hook instalado.")

        self._patch_webtorrent_path(wrap_sh)

    def _install_system_deps(self, packages: list[str]) -> None:
        """Install missing system packages via the available package manager."""
        missing = [p for p in packages if not shutil.which(p)]
        if not missing:
            return

        typer.echo(f"Instalando dependências do sistema: {', '.join(missing)}")

        for mgr, cmd in [
            ("pacman", ["sudo", "pacman", "-S", "--noconfirm"]),
            ("apt-get", ["sudo", "apt-get", "install", "-y"]),
            ("dnf", ["sudo", "dnf", "install", "-y"]),
        ]:
            if shutil.which(mgr):
                result = subprocess.run([*cmd, *missing], check=False)
                if result.returncode != 0:
                    raise PlaybackError(f"Falha ao instalar {missing} via {mgr}")
                return

        raise PlaybackError(
            f"Gerenciador de pacotes não suportado. Instale manualmente: {', '.join(missing)}"
        )

    def _install_webtorrent_cli(self) -> None:
        """Install webtorrent-cli via npm if not present."""
        if shutil.which("webtorrent"):
            return

        if not shutil.which("npm"):
            raise PlaybackError(
                "npm não encontrado. Instale Node.js para continuar."
            )

        typer.echo("Instalando webtorrent-cli via npm...")
        result = subprocess.run(
            ["npm", "install", "-g", "webtorrent-cli"], check=False
        )
        if result.returncode != 0:
            raise PlaybackError("Falha ao instalar webtorrent-cli via npm")

    def _clone_hook(self, hook_dir: Path) -> None:
        """Clone mpv-webtorrent-hook into the mpv scripts directory."""
        if not shutil.which("git"):
            raise PlaybackError("git não encontrado. Instale git para continuar.")

        hook_dir.parent.mkdir(parents=True, exist_ok=True)
        typer.echo(f"Clonando mpv-webtorrent-hook em {hook_dir}...")
        result = subprocess.run(
            [
                "git", "clone",
                "https://github.com/noctuid/mpv-webtorrent-hook",
                str(hook_dir),
            ],
            check=False,
        )
        if result.returncode != 0:
            raise PlaybackError("Falha ao clonar mpv-webtorrent-hook")

    def _patch_webtorrent_path(self, wrap_sh: Path) -> None:
        """Patch webtorrent-wrap.sh to use the absolute webtorrent binary path.

        mpv scripts may not inherit the user's full PATH (e.g. mise-managed bins),
        so we replace the bare `webtorrent` call with the resolved absolute path.
        """
        webtorrent_bin = shutil.which("webtorrent")
        if not webtorrent_bin:
            raise PlaybackError(
                "webtorrent não encontrado no PATH após instalação."
            )

        content = wrap_sh.read_text()
        # Already patched with this exact binary — nothing to do
        if webtorrent_bin in content:
            return

        patched = content.replace("webtorrent download", f"{webtorrent_bin} download", 1)
        if patched == content:
            return  # pattern not found, skip silently

        wrap_sh.write_text(patched)
        wrap_sh.chmod(0o755)

    def play_torrent(
        self,
        magnet_link: str,
        title: Title,
        episode: Optional[int] = None,
    ) -> None:
        """Stream and play a torrent using mpv with mpv-webtorrent-hook.

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
            self._stream_with_mpv(magnet_link)
            typer.echo(f"✓ Playback completed: {display_name}")

        except KeyboardInterrupt:
            typer.echo("\n⏹️  Playback interrupted")
            raise
        except Exception as e:
            raise PlaybackError(f"Playback failed: {e}") from e

    def _stream_with_mpv(self, magnet_link: str) -> None:
        """Stream torrent directly with mpv (via mpv-webtorrent-hook).

        Requires mpv-webtorrent-hook to be installed:
        https://github.com/noctuid/mpv-webtorrent-hook

        Args:
            magnet_link: Magnet link to stream

        Raises:
            PlaybackError: If process fails
        """
        # Prefix with webtorrent:// so the hook identifies it as a torrent
        # without prepending the current working directory to the path
        torrent_uri = f"webtorrent://{magnet_link}" if not magnet_link.startswith("webtorrent://") else magnet_link
        cmd = ["mpv", torrent_uri]

        try:
            result = subprocess.run(cmd, check=False, capture_output=False)
            if result.returncode not in (0, 143):  # 143 is SIGTERM (user interrupt)
                raise PlaybackError(
                    f"Playback process exited with code {result.returncode}"
                )

        except FileNotFoundError as e:
            raise PlaybackError(f"Failed to start mpv: {e}") from e
