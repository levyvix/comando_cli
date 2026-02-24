# Design: Streaming CLI Architecture

## Context
- **Target users**: Linux users comfortable with CLI tools
- **Primary data source**: gratistorrent.com (Cloudflare-protected)
- **Playback requirement**: Local torrent download + streaming via mpv
- **UX preference**: Interactive CLI with fzf for selection, sequential menus for options

## Goals
- Minimal, focused implementation for gratistorrent.com scraping
- Seamless streaming experience (torrent → local playback)
- Reliable Cloudflare bypass using Scrapling's StealthyFetcher
- Extensible architecture for future website additions
- Efficient torrent streaming without full pre-download requirement

### Non-Goals
- Support for multiple websites initially (start with gratistorrent.com)
- Web UI or GUI
- Automatic quality detection
- Subtitle downloading or management
- User accounts or authentication

## Decisions

### 1. Data Source & Scraping
**Decision**: Use Scrapling's StealthyFetcher with solve_cloudflare=True
- Handles Cloudflare challenges transparently
- Reliable headless browser simulation
- Less maintenance than manual CF bypass logic
- Trade-off: Slower than direct HTTP, but necessary for gratistorrent.com

### 2. Torrent Streaming Architecture
**Decision**: webtorrent (local) → mpv (playback)
- Download to temp directory: ~/.cache/comando-cli/torrents/
- mpv plays from local file as it downloads
- Cleanup after playback completes
- Trade-off: Requires local disk space; alternative (HTTP streaming via webtorrent-cli) is experimental

### 3. Episode Selection
**Decision**: Flexible CLI syntax with validation
- `-e 2`: Episode 2
- `-e 2-5`: Episodes 2 through 5
- `-e 2-`: Episodes 2 to end
- `-e -5`: Episodes 1 through 5
- Stored in watch history as "last watched episode" for resume

### 4. Quality/Language Selection
**Decision**: Sequential interactive menus (not fzf)
- Step 1: "Select quality" menu (720p, 1080p, etc.)
- Step 2: "Select language" menu (Portuguese, English, etc.)
- Simpler UX than flat fzf list; easier to reason about
- Trade-off: More steps vs. single selection

### 5. Watch History
**Decision**: SQLite database in ~/.config/comando-cli/history.db
- Track: title, media_type (movie/series), last_episode (for series), last_watched_date
- Update on playback completion
- Allow quick resume with `comando watch --resume`
- Trade-off: Adds dependency (sqlite3); alternative (JSON) is simpler but slower for queries

### 6. Configuration
**Decision**: XDG Base Directory Specification compliance
- Config: ~/.config/comando-cli/config.toml
- Cache: ~/.cache/comando-cli/
- Data: ~/.local/share/comando-cli/ (for SQLite history)
- Benefit: Respects user system standards
- Future: Allow override via CLI flags

### 7. Error Handling
**Decision**: Graceful failures with user-friendly messages
- Cloudflare block → retry with backoff
- Invalid torrent/magnet → show error, prompt for manual selection
- Network errors → clear messaging on what went wrong
- Incomplete torrent → warn user, offer retry

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Cloudflare blocking scraper | Use Scrapling with latest browser fingerprints; implement rate limiting |
| Large torrent files | Warn before download; allow cancellation; clear cache on exit |
| Episode metadata incomplete | Fall back to default sorting; show raw episode count |
| webtorrent stalls | Monitor playback; auto-retry with different magnet if available |

## Alternative Considered

### Alternative: HTTP Streaming via webtorrent-cli
- Stream torrents via HTTP server instead of local files
- Benefit: No disk space requirement
- Trade-off: webtorrent-cli stability concerns; extra process overhead
- Decision: Start with local download; can revisit later if disk space becomes issue

## Future Extensions (Out of Scope)
- Support for comando.la (after gratistorrent.com stable)
- Quality auto-selection based on available bandwidth
- Subtitle fetching
- Playback resume at last watched position (beyond episode level)
