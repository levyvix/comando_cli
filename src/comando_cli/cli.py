"""Command-line interface for Comando CLI."""

import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import requests
import typer

from comando_cli import __version__
from comando_cli.config import ensure_directories
from comando_cli.db import Database
from comando_cli.episode_selector import parse_episode_syntax
from comando_cli.fuzzy import select_with_fzf
from comando_cli.models import MediaType
from comando_cli.playback import PlaybackError, TorrentPlayer, _is_video_file
from comando_cli.quality_selector import (
    select_episode_magnet,
    select_quality_and_language,
    select_title,
    select_torrent_file,
)
from comando_cli.scraper import ComandoLaScraper, GratistorrentScraper, ScraperError

app = typer.Typer(
    help="Comando CLI - Stream movies and TV series from the command line.",
    invoke_without_command=True,
)

# Initialize database
config = ensure_directories()
db = Database(config.data_dir / "history.db")
_scraper_override: Optional[str] = None
_POST_PLAYBACK_ACTIONS = [
    ("proximo", "Próximo"),
    ("anterior", "Anterior"),
    ("replay", "Replay"),
    ("search", "Voltar para busca"),
    ("exit", "Sair"),
]
REMOTE_PYPROJECT_URL = (
    "https://raw.githubusercontent.com/levyvix/comando_cli/master/pyproject.toml"
)
REMOTE_TAGS_URL = "https://api.github.com/repos/levyvix/comando_cli/tags?per_page=50"
REMOTE_INSTALLER_URL = (
    "https://raw.githubusercontent.com/levyvix/comando_cli/master/install-cli.py"
)


def _make_scraper():
    """Instantiate scraper based on config."""
    scraper_source = _scraper_override or config.scraper
    if scraper_source == "gratistorrent":
        return GratistorrentScraper()
    return ComandoLaScraper()


@app.callback()
def main(
    comando: bool = typer.Option(
        False,
        "--comando",
        help="Use o site comando.la como fonte de busca neste comando.",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Global CLI options."""
    global _scraper_override
    if version:
        typer.echo(f"comando-cli {__version__}")
        raise typer.Exit()
    _scraper_override = "comando_la" if comando else None


def _extract_remote_version(pyproject_text: str) -> Optional[str]:
    """Extract [project] version from pyproject.toml content."""
    match = re.search(r'^version\s*=\s*"([^"]+)"\s*$', pyproject_text, re.MULTILINE)
    return match.group(1) if match else None


def _normalize_version(version: str) -> str:
    """Normalize version string for comparisons."""
    return version.strip().removeprefix("v")


def _version_key(version: str) -> tuple[tuple[int, int | str], ...]:
    """Normalize versions for a simple semantic-ish comparison."""
    tokens = re.split(r"[.\-+]", _normalize_version(version))
    key: list[tuple[int, int | str]] = []
    for token in tokens:
        if token.isdigit():
            key.append((0, int(token)))
        else:
            key.append((1, token.lower()))
    return tuple(key)


def _fetch_remote_version() -> str:
    """Read latest version from repository tags and pyproject on master."""
    discovered_versions: list[str] = []

    try:
        response = requests.get(REMOTE_TAGS_URL, timeout=10)
        response.raise_for_status()
        tags_payload = response.json()
        if isinstance(tags_payload, list):
            for tag in tags_payload:
                if not isinstance(tag, dict):
                    continue
                tag_name = tag.get("name")
                if not isinstance(tag_name, str):
                    continue
                normalized = _normalize_version(tag_name)
                if re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.\-]+)?", normalized):
                    discovered_versions.append(normalized)
    except (requests.RequestException, ValueError, TypeError):
        pass

    try:
        response = requests.get(REMOTE_PYPROJECT_URL, timeout=10)
        response.raise_for_status()
        remote_version = _extract_remote_version(response.text)
        if remote_version:
            discovered_versions.append(remote_version)
    except (requests.RequestException, TypeError, ValueError):
        pass

    if not discovered_versions:
        raise ValueError("Could not parse version from remote sources")
    return max(discovered_versions, key=_version_key)


def _run_remote_installer() -> None:
    """Download and run the upstream installer script."""
    response = requests.get(REMOTE_INSTALLER_URL, timeout=15)
    response.raise_for_status()

    with tempfile.TemporaryDirectory() as tmp_dir:
        installer_path = Path(tmp_dir) / "install-cli.py"
        installer_path.write_text(response.text, encoding="utf-8")
        subprocess.run([sys.executable, str(installer_path)], check=True)


@app.command()
def update(
    check: bool = typer.Option(
        False,
        "--check",
        help="Only check if a newer version is available.",
    ),
    yes: bool = typer.Option(
        False,
        "-y",
        "--yes",
        help="Update without confirmation prompt.",
    ),
) -> None:
    """Check for updates and install the latest version."""
    typer.echo(f"Current version: {__version__}")
    try:
        remote_version = _fetch_remote_version()
    except (requests.RequestException, ValueError) as e:
        typer.echo(f"❌ Could not check remote version: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Remote version: {remote_version}")
    has_update = _version_key(remote_version) > _version_key(__version__)

    if not has_update:
        typer.echo("✅ You are already on the latest version.")
        return

    typer.echo("⬆️  Update available.")
    if check:
        return

    if not yes and not typer.confirm("Install update now?", default=True):
        typer.echo("Update canceled.")
        return

    typer.echo("📦 Installing update...")
    try:
        _run_remote_installer()
    except (requests.RequestException, OSError, subprocess.CalledProcessError) as e:
        typer.echo(f"❌ Update failed: {e}", err=True)
        raise typer.Exit(1)

    typer.echo("✅ Update finished. Run `com --version` to verify.")


@app.command()
def search(query: str = typer.Argument(..., help="Search query")) -> None:
    """Search for movies and TV series on gratistorrent.com."""
    if not query:
        typer.echo("Search query cannot be empty")
        return

    try:
        typer.echo(f"🔍 Searching for: {query}...")

        scraper = _make_scraper()
        results = scraper.search(query)

        if not results:
            typer.echo("❌ No results found")
            return

        typer.echo(f"\n✓ Found {len(results)} result(s):\n")
        for i, title in enumerate(results, 1):
            typer.echo(f"{i}. {title.name} ({title.media_type.value})")

    except ScraperError as e:
        typer.echo(f"❌ Search error: {e}", err=True)
        raise typer.Exit(1)


def _play_consolidated(
    title_detail,
    quality_option,
    episodes_to_play: list[int],
    player,
    prompt_start_file: bool = False,
) -> None:
    """Play a consolidated torrent as an mpv playlist starting from the requested episode."""
    typer.echo("📦 Consolidated torrent detected — resolving file list...")
    try:
        torrent_files = player.list_torrent_files(quality_option.magnet_link)
    except Exception as e:
        typer.echo(f"⚠️  Could not resolve file list ({e}). Playing from the start.")
        player.play_torrent(quality_option.magnet_link, title_detail)
        db.add_watch_record(
            title_id=title_detail.id,
            title_name=title_detail.name,
            media_type=title_detail.media_type,
            title_url=title_detail.url,
            last_episode=episodes_to_play[0] if episodes_to_play else None,
        )
        return

    video_files = [f for f in torrent_files if _is_video_file(f.path)]
    if not video_files:
        video_files = torrent_files  # fallback: try all files

    # Sort by episode number, then path
    video_files_sorted = sorted(
        video_files,
        key=lambda f: (f.episode if f.episode is not None else 9999, f.path),
    )

    typer.echo(f"✓ Found {len(video_files_sorted)} video file(s) in torrent:")
    for f in video_files_sorted:
        ep_label = f"Ep.{f.episode:02d}" if f.episode is not None else "   "
        typer.echo(f"  [{ep_label}] {f.path.split('/')[-1]}")

    # Determine which file to start from
    start_episode = episodes_to_play[0] if episodes_to_play else None
    start_file = None
    if prompt_start_file:
        typer.echo("\n🧲 Escolha qual torrent/arquivo iniciar:")
        start_file = select_torrent_file(video_files_sorted)
        if not start_file:
            typer.echo("❌ No torrent/file selected")
            return
    else:
        if start_episode is not None:
            start_file = next(
                (f for f in video_files_sorted if f.episode == start_episode), None
            )
        if start_file is None:
            start_file = video_files_sorted[0] if video_files_sorted else None

    if not start_file:
        typer.echo("❌ No video files found in torrent")
        return

    # webtorrent --playlist rotates the file list to start_index and opens
    # all files in mpv — the user navigates episodes natively with > / ]
    player.play_torrent_playlist(
        quality_option.magnet_link,
        start_index=start_file.index,
        title=title_detail,
        start_episode=start_file.episode,
    )
    db.add_watch_record(
        title_id=title_detail.id,
        title_name=title_detail.name,
        media_type=title_detail.media_type,
        title_url=title_detail.url,
        last_episode=start_file.episode,
    )


def _option_covers(opt, ep_num: int) -> bool:
    """Return True if a quality option covers the given episode number."""
    if opt.episode is None:
        return True
    return opt.episode <= ep_num <= (opt.episode_end or opt.episode)


def _select_post_playback_action() -> str:
    """Show post-playback action menu and return selected action key."""
    labels = [label for _, label in _POST_PLAYBACK_ACTIONS]
    label_to_action = {label: action for action, label in _POST_PLAYBACK_ACTIONS}

    selected = select_with_fzf(labels, prompt="Playback finalizado> ", height="40%")
    if selected is not None:
        return label_to_action.get(selected, "exit")

    typer.echo("\n📺 O que deseja fazer?")
    for idx, label in enumerate(labels, 1):
        typer.echo(f"  {idx}. {label}")
    try:
        choice = typer.prompt("Enter choice (number)", type=int)
        if 1 <= choice <= len(_POST_PLAYBACK_ACTIONS):
            return _POST_PLAYBACK_ACTIONS[choice - 1][0]
    except (ValueError, KeyboardInterrupt):
        pass
    return "exit"


def _play_title(title_detail, episodes: Optional[str], scraper) -> bool:
    """Core play logic shared between watch and resume commands."""
    episodes_to_play: list[int] = []
    episodes_explicitly_provided = episodes is not None
    if title_detail.media_type == MediaType.SERIES:
        # total_episodes must account for episode_end ranges
        total_episodes = (
            max(
                (opt.episode_end or opt.episode)
                for opt in title_detail.quality_options
                if opt.episode is not None
            )
            if any(opt.episode for opt in title_detail.quality_options)
            else 1
        )

        if episodes:
            try:
                episode_range = parse_episode_syntax(episodes, total_episodes)
                typer.echo(f"✓ Episodes: {episode_range.episodes}")
                episodes_to_play = episode_range.episodes
            except Exception as e:
                typer.echo(f"❌ Invalid episode syntax: {e}", err=True)
                return False
        else:
            typer.echo("✓ No episode specified, playing from episode 1")
            episode_range = parse_episode_syntax("1-", total_episodes)
            episodes_to_play = episode_range.episodes

    first_episode = episodes_to_play[0] if episodes_to_play else None
    quality_option = select_quality_and_language(title_detail, episode=first_episode)
    if not quality_option:
        typer.echo("❌ No quality selected")
        return False

    magnet_to_save = (
        quality_option.magnet_link
        if title_detail.media_type == MediaType.MOVIE
        else None
    )
    db.add_watch_record(
        title_id=title_detail.id,
        title_name=title_detail.name,
        media_type=title_detail.media_type,
        title_url=title_detail.url,
        magnet_url=magnet_to_save,
        last_episode=first_episode,
    )

    player = TorrentPlayer(config)

    if not episodes_to_play:
        # Movie
        player.play_torrent(quality_option.magnet_link, title_detail, episode=None)
        return False

    if quality_option.episode is None:
        # Fully consolidated magnet (one torrent = all episodes)
        _play_consolidated(
            title_detail,
            quality_option,
            episodes_to_play,
            player,
            prompt_start_file=(
                title_detail.media_type == MediaType.SERIES
                and not episodes_explicitly_provided
            ),
        )
        return False

    if title_detail.media_type == MediaType.SERIES and not episodes_explicitly_provided:
        compatible_options = [
            opt
            for opt in title_detail.quality_options
            if opt.episode is not None
            and opt.quality == quality_option.quality
            and opt.language == quality_option.language
        ]
        if compatible_options:
            typer.echo("\n🧲 Escolha o torrent/episódio inicial:")
            chosen = select_episode_magnet(compatible_options)
            if not chosen:
                typer.echo("❌ No torrent selected")
                return False
            if chosen.episode is not None:
                episodes_to_play = [
                    ep for ep in episodes_to_play if ep >= chosen.episode
                ]

    # Series with per-magnet options (single or multi-episode per magnet).
    # Walk episodes_to_play in order; collect consecutive episodes that share
    # the same magnet, then play each magnet group.
    idx = 0
    while idx < len(episodes_to_play):
        ep_num = episodes_to_play[idx]
        ep_option = next(
            (
                opt
                for opt in title_detail.quality_options
                if _option_covers(opt, ep_num)
                and opt.quality == quality_option.quality
                and opt.language == quality_option.language
            ),
            None,
        )
        if not ep_option:
            typer.echo(
                f"⚠️  No {quality_option.quality} {quality_option.language} option for episode {ep_num}, skipping"
            )
            idx += 1
            continue

        try:
            if ep_option.episode_end is not None:
                # Multi-episode magnet — use consolidated playlist approach
                _play_consolidated(
                    title_detail, ep_option, episodes_to_play[idx:], player
                )
            else:
                # Single-episode magnet
                player.play_torrent(ep_option.magnet_link, title_detail, episode=ep_num)
                db.add_watch_record(
                    title_id=title_detail.id,
                    title_name=title_detail.name,
                    media_type=title_detail.media_type,
                    title_url=title_detail.url,
                    last_episode=ep_num,
                )
        except KeyboardInterrupt:
            typer.echo("\n⏹️  Stopped")
            break

        action = _select_post_playback_action()
        if action == "search":
            return True
        if action == "exit":
            break
        if action == "replay":
            continue
        if action == "anterior":
            if idx == 0:
                typer.echo("⚠️  Already at first episode")
                continue
            idx -= 1
            continue

        if ep_option.episode_end is not None:
            next_idx = next(
                (
                    i
                    for i in range(idx + 1, len(episodes_to_play))
                    if episodes_to_play[i] > ep_option.episode_end
                ),
                len(episodes_to_play),
            )
            idx = next_idx
        else:
            idx += 1

    return False


@app.command()
def watch(
    title_query: str = typer.Argument(..., help="Title name or search query"),
    episodes: Optional[str] = typer.Option(
        None,
        "-e",
        "--episodes",
        help="Episode(s) for series: single (2), range (2-5), open range (2-), or prefix (-5)",
    ),
) -> None:
    """Search and watch a title."""
    if not title_query:
        typer.echo("❌ Title query cannot be empty")
        return

    try:
        scraper = _make_scraper()
        while True:
            typer.echo(f"🔍 Searching for: {title_query}")
            results = scraper.search(title_query)

            if not results:
                typer.echo("❌ No results found")
                return

            title = select_title(results)
            if not title:
                typer.echo("❌ No title selected")
                return
            typer.echo(f"\n✓ Selected: {title.name} ({title.media_type.value})")

            # Fetch metadata
            typer.echo("📥 Fetching metadata...")
            title_detail = scraper.fetch_metadata(title.url)

            if not title_detail:
                typer.echo("❌ Failed to fetch metadata")
                return

            should_return_to_search = _play_title(title_detail, episodes, scraper)
            if should_return_to_search:
                typer.echo("↩️  Returning to search...")
                continue
            break

    except ScraperError as e:
        typer.echo(f"❌ Scraper error: {e}", err=True)
        raise typer.Exit(1)
    except PlaybackError as e:
        typer.echo(f"❌ Playback error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def history() -> None:
    """Show watch history."""
    try:
        records = db.get_all_watch_history()

        if not records:
            typer.echo("📭 No watch history yet")
            return

        typer.echo("\n📺 Watch History:\n")
        for i, record in enumerate(records, 1):
            episode_info = (
                f" (Ep. {record.last_episode})" if record.last_episode else ""
            )
            typer.echo(
                f"{i}. {record.title_name}{episode_info} - {record.last_watched_date.strftime('%Y-%m-%d %H:%M')}"
            )

    except Exception as e:
        typer.echo(f"❌ Error reading history: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def resume() -> None:
    """Resume watching the last title."""
    try:
        last_watch = db.get_last_watched()

        if not last_watch:
            typer.echo("📭 No watch history to resume")
            return

        typer.echo(f"▶️  Resuming: {last_watch.title_name}")

        scraper = _make_scraper()

        if last_watch.media_type == MediaType.MOVIE and last_watch.magnet_url:
            # Movie with saved magnet: play directly without re-fetching
            from comando_cli.models import Title

            title_stub = Title(
                id=last_watch.title_id,
                name=last_watch.title_name,
                media_type=last_watch.media_type,
                url=last_watch.title_url or "",
            )
            player = TorrentPlayer(config)
            player.play_torrent(last_watch.magnet_url, title_stub, episode=None)

        elif last_watch.title_url:
            # Series (or movie without magnet): re-fetch metadata from saved URL
            typer.echo("📥 Fetching metadata...")
            title_detail = scraper.fetch_metadata(last_watch.title_url)
            if not title_detail:
                typer.echo("❌ Failed to fetch metadata")
                return

            # For series: suggest continuing from next episode
            next_episode = None
            if last_watch.last_episode:
                next_episode = str(last_watch.last_episode + 1)
                typer.echo(f"✓ Continuing from episode {next_episode}")

            _play_title(title_detail, next_episode, scraper)

        else:
            typer.echo("❌ No URL saved for this title. Please search and watch again.")

    except ScraperError as e:
        typer.echo(f"❌ Scraper error: {e}", err=True)
        raise typer.Exit(1)
    except PlaybackError as e:
        typer.echo(f"❌ Playback error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Error resuming: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
