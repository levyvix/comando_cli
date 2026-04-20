## Architecture

The app is structured as a pipeline: CLI → Selection UI → Scraper → Playback → DB persistence.

**Entry point**: `src/comando_cli/cli.py` — four Typer commands: `search`, `watch`, `history`, `resume`

**Data flow for `watch`**:
1. `cli.py` calls `scraper.py` to search titles on gratistorrent.com
2. User selects quality/language via `quality_selector.py` (interactive menus)
3. For series: `episode_selector.py` parses range syntax (`2`, `2-5`, `2-`, `-5`)
4. `playback.py` spawns WebTorrent CLI + MPV for streaming
5. `db.py` records watch history to SQLite at `~/.local/share/comando_cli/history.db`

## **Scrapers** (`scraper.py`): Two implementations — `GratistorrentScraper` (primary) and `ComandoLaScraper` (alternative). Both return `Title` Pydantic models with magnet links.

**Migrations** (`migrations/`): yoyo-migrations with SQLite. Auto-run on DB init via `migrations.py`. Add new migrations as `00N_description.py`.

**Config** (`config.py`): XDG Base Directory compliant. Config at `~/.config/comando_cli/`, data at `~/.local/share/comando_cli/`, cache at `~/.cache/comando_cli/`.

## External Dependencies

These system tools must be installed separately:
- `mpv` — video player
- `webtorrent-cli` — torrent streaming (`npm install -g webtorrent-cli`)
- `jq`, `xidel` — used in playback helpers

## Key Models (`models.py`)

- `Title` — scraped result with name, URL, media type, quality options
- `QualityOption` — quality + language + magnet link
- `MediaType` — `movie` | `series` enum
- `WatchHistory` — DB record tracking last episode, position, timestamps
