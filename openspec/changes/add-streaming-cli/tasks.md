# Implementation Tasks: Streaming CLI

## 1. Project Setup
- [x] 1.1 Add dependencies to pyproject.toml (scrapling, webtorrent, pydantic, click for CLI)
- [x] 1.2 Create project structure (src/comando_cli/ with __init__.py, config.py, models.py)
- [x] 1.3 Setup XDG Base Directory helpers (config_dir, cache_dir, data_dir functions)
- [x] 1.4 Create config file with defaults (~/.config/comando-cli/config.toml)
- [x] 1.5 Validate setup with `uv run main.py --help` shows basic help

## 2. Web Scraping Engine
- [x] 2.1 Create scraper module (src/comando_cli/scraper.py)
- [x] 2.2 Implement Scrapling Fetcher (no Cloudflare bypass needed for site)
- [x] 2.3 Create search function: query string → list of titles with metadata
- [x] 2.4 Parse search results: extract title, URL, media_type (movie/series)
- [x] 2.5 Create metadata fetcher: fetch title page → episodes list, poster, synopsis
- [ ] 2.6 Write unit tests for scraper (mock Scrapling responses)
- [ ] 2.7 Study site structure with playwright-cli and refine HTML parsing patterns

## 3. Data Models & Storage
- [x] 3.1 Create models.py: Title, Episode, QualityOption, WatchHistory classes
- [x] 3.2 Setup SQLite database schema (titles, watch_history tables)
- [x] 3.3 Create database module (src/comando_cli/db.py) with CRUD operations
- [x] 3.4 Implement watch history tracking: add_watch_record(), get_last_watched()
- [ ] 3.5 Write unit tests for database operations
- [ ] 3.6 Verify schema migrations work correctly

## 4. Episode Selection
- [x] 4.1 Create episode_selector.py module
- [x] 4.2 Implement parser for -e flag: "2", "2-5", "2-", "-5" → episode list
- [x] 4.3 Validate episode ranges against actual episode count
- [x] 4.4 Create error messages for invalid ranges
- [ ] 4.5 Write unit tests for episode selector (all range formats)
- [ ] 4.6 Manual test: series with 10 episodes, test all range formats

## 5. Quality & Language Selection
- [x] 5.1 Create quality_selector.py module
- [x] 5.2 Extract quality options from fetched title page (720p, 1080p, etc.)
- [x] 5.3 Extract language options from fetched title page
- [x] 5.4 Implement interactive menu: quality selection (list of options)
- [x] 5.5 Implement interactive menu: language selection (list of options)
- [x] 5.6 Return selected magnet link from combined selection
- [ ] 5.7 Write unit tests for menu flow
- [ ] 5.8 Manual test: select different quality/language combinations

## 6. Torrent Streaming & Playback
- [x] 6.1 Create playback.py module
- [x] 6.2 Implement webtorrent wrapper: magnet link → local file download
- [x] 6.3 Implement file monitoring: detect when file is playable (first chunk available)
- [x] 6.4 Launch mpv with local file path
- [x] 6.5 Implement graceful cleanup: kill webtorrent after mpv closes
- [x] 6.6 Add error handling: network errors, invalid torrents, stalled downloads
- [ ] 6.7 Write tests for playback flow (mock webtorrent/mpv)
- [ ] 6.8 Manual test: actual torrent streaming to completion

## 7. CLI Interface
- [x] 7.1 Create cli.py module using Typer framework
- [x] 7.2 Implement `comando search <query>` command
- [x] 7.3 Implement `comando watch <title>` command
- [x] 7.4 Add `-e <episodes>` flag for series selection
- [x] 7.5 Integrate quality/language menus into watch flow
- [x] 7.6 Add `comando history` command to show watch history
- [x] 7.7 Add `comando resume` command
- [x] 7.8 Add `--help` and verbose output
- [ ] 7.9 Write integration tests for full CLI flow
- [ ] 7.10 Manual test: full user journey (needs live magnet link)

## 8. Integration & Polish
- [ ] 8.1 Update main.py to route to CLI entry point
- [ ] 8.2 Create ~/.config/comando-cli/ on first run
- [ ] 8.3 Handle edge cases: no results, invalid episodes, interrupted playback
- [ ] 8.4 Add debug logging (--verbose flag)
- [ ] 8.5 Test with actual gratistorrent.com content
- [ ] 8.6 Verify Cloudflare bypass works consistently
- [ ] 8.7 Performance test: search time, metadata fetch time
- [ ] 8.8 Documentation: basic README with usage examples

## 9. Testing & Validation
- [ ] 9.1 Unit tests coverage: scraper, db, episode_selector, quality_selector (>80%)
- [ ] 9.2 Integration tests: full search → play flow
- [ ] 9.3 E2E tests with Playwright: actual browser interaction (if needed for verification)
- [ ] 9.4 Manual regression testing on Linux system
- [ ] 9.5 Verify watch history persists across sessions
- [ ] 9.6 Check cache cleanup after playback

## Notes
- Tasks 2-6 can be developed in parallel (separate modules)
- Task 1 must complete first
- Task 7 depends on 2-6 being mostly complete
- Manual testing at each major phase recommended
- **NEXT PRIORITY**: Use `playwright-cli` to study gratistorrent.com site structure
  - Study search results page HTML structure
  - Study title/episode page layout
  - Identify CSS selectors for titles, episodes, quality options, magnet links
  - Update regex patterns in scraper based on findings
- HTML parsing patterns need refinement after site structure analysis
- System dependencies needed: webtorrent-cli, mpv (install with system package manager)
