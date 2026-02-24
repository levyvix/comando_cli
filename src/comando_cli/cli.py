"""Command-line interface for Comando CLI."""

from typing import Optional

import typer

from .config import ensure_directories, load_config
from .db import Database
from .episode_selector import parse_episode_syntax
from .models import MediaType
from .playback import PlaybackError, TorrentPlayer
from .quality_selector import select_quality_and_language, select_title
from .scraper import GratistorrentScraper, ScraperError

app = typer.Typer(help="Comando CLI - Stream movies and TV series from the command line.")

# Global state for config and database
config = None
db = None


@app.callback()
def setup(verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")) -> None:
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

        scraper = GratistorrentScraper()
        results = scraper.search(query)

        if not results:
            typer.echo("❌ No results found")
            return

        typer.echo(f"\n✓ Found {len(results)} result(s):\n")
        for i, title in enumerate(results, 1):
            typer.echo(f"{i}. {title.name} ({title.media_type.value})")

        # Interactive selection with fzf would go here
        # For now, just show results

    except ScraperError as e:
        typer.echo(f"❌ Search error: {e}", err=True)
        raise typer.Exit(1)


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

        scraper = GratistorrentScraper()
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

        # Handle episodes for series
        episodes_to_play: list[int] = []
        if title_detail.media_type == MediaType.SERIES:
            # Infer total episodes from quality options (each has an episode number)
            episode_numbers = set()
            for opt in title_detail.quality_options:
                if opt.episode:
                    episode_numbers.add(opt.episode)
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

        # Select quality and language for the first episode (or movie)
        first_episode = episodes_to_play[0] if episodes_to_play else None
        quality_option = select_quality_and_language(title_detail, episode=first_episode)
        if not quality_option:
            typer.echo("❌ No quality selected")
            return

        # Record in watch history
        db.add_watch_record(
            title_id=title_detail.id,
            title_name=title_detail.name,
            media_type=title_detail.media_type,
        )

        player = TorrentPlayer(config)

        if not episodes_to_play:
            # Movie: play directly
            player.play_torrent(quality_option.magnet_link, title_detail, episode=None)
        else:
            # Series: play each episode, reusing same quality+language for subsequent ones
            for i, ep_num in enumerate(episodes_to_play):
                if i == 0:
                    ep_option = quality_option
                else:
                    # Auto-select same quality+language for this episode
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
                except KeyboardInterrupt:
                    typer.echo("\n⏹️  Stopped")
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
            episode_info = f" (Ep. {record.last_episode})" if record.last_episode else ""
            typer.echo(f"{i}. {record.title_name}{episode_info} - {record.last_watched_date.strftime('%Y-%m-%d %H:%M')}")

    except Exception as e:
        typer.echo(f"❌ Error reading history: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def resume() -> None:
    """Resume watching the last episode."""
    try:
        last_watch = db.get_last_watched()

        if not last_watch:
            typer.echo("📭 No watch history to resume")
            return

        typer.echo(f"▶️  Resuming: {last_watch.title_name}")
        # Full resumption logic would go here

    except Exception as e:
        typer.echo(f"❌ Error resuming: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
