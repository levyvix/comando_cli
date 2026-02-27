"""Command-line interface for Comando CLI."""

from typing import Optional

import typer

from .config import ensure_directories
from .db import Database
from .episode_selector import parse_episode_syntax
from .models import MediaType
from .playback import PlaybackError, TorrentPlayer, _is_video_file
from .quality_selector import select_quality_and_language, select_title
from .scraper import ComandoLaScraper, GratistorrentScraper, ScraperError

app = typer.Typer(
    help="Comando CLI - Stream movies and TV series from the command line."
)

# Global state for config and database
config = None
db = None


def _make_scraper():
    """Instantiate scraper based on config."""
    if config and config.scraper == "gratistorrent":
        return GratistorrentScraper()
    return ComandoLaScraper()


@app.callback()
def setup(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
) -> None:
    """Initialize application."""
    global config, db

    config = ensure_directories()
    if verbose:
        config.verbose = True

    # Initialize database
    db = Database(config.data_dir / "history.db")


@app.command()
def search(query: str = typer.Argument(..., help="Search query")) -> None:
    """Search for movies and TV series on gratistorrent.com."""
    if not query:
        typer.echo("❌ Search query cannot be empty")
        return

    try:
        typer.echo(f"🔍 Searching for: {query}")

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


def _play_consolidated(title_detail, quality_option, episodes_to_play: list[int], player) -> None:
    """Play a consolidated torrent as an mpv playlist starting from the requested episode."""
    typer.echo("📦 Consolidated torrent detected — resolving file list...")
    torrent_files = player.list_torrent_files(quality_option.magnet_link)

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


def _play_title(title_detail, episodes: Optional[str], scraper) -> None:
    """Core play logic shared between watch and resume commands."""
    episodes_to_play: list[int] = []
    if title_detail.media_type == MediaType.SERIES:
        episode_numbers = {
            opt.episode for opt in title_detail.quality_options if opt.episode
        }
        total_episodes = max(episode_numbers) if episode_numbers else 1

        if episodes:
            try:
                episode_range = parse_episode_syntax(episodes, total_episodes)
                typer.echo(f"✓ Episodes: {episode_range.episodes}")
                episodes_to_play = episode_range.episodes
            except Exception as e:
                typer.echo(f"❌ Invalid episode syntax: {e}", err=True)
                return
        else:
            typer.echo("✓ No episode specified, starting from first available")
            episodes_to_play = [1]

    first_episode = episodes_to_play[0] if episodes_to_play else None
    quality_option = select_quality_and_language(title_detail, episode=first_episode)
    if not quality_option:
        typer.echo("❌ No quality selected")
        return

    # Save to history with URLs
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
        # Movie: play directly
        player.play_torrent(quality_option.magnet_link, title_detail, episode=None)
    elif quality_option.episode is None and title_detail.media_type == MediaType.SERIES:
        # Consolidated magnet: single torrent contains all episode files
        _play_consolidated(title_detail, quality_option, episodes_to_play, player)
    else:
        # Per-episode magnets: play each individually
        for i, ep_num in enumerate(episodes_to_play):
            if i == 0:
                ep_option = quality_option
            else:
                ep_option = next(
                    (
                        opt
                        for opt in title_detail.quality_options
                        if opt.episode == ep_num
                        and opt.quality == quality_option.quality
                        and opt.language == quality_option.language
                    ),
                    None,
                )
                if not ep_option:
                    typer.echo(
                        f"⚠️  No {quality_option.quality} {quality_option.language} option for episode {ep_num}, skipping"
                    )
                    continue

            try:
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
        typer.echo(f"🔍 Searching for: {title_query}")

        scraper = _make_scraper()
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

        _play_title(title_detail, episodes, scraper)

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
            from .models import Title

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
