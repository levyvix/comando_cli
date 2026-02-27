# Project Context

## Purpose
CLI tool for streaming movies and TV series from gratistorrent.com. Allows users to search, browse, select quality/language, and play content via webtorrent.

## Tech Stack
- Python 3.12+
- Typer (CLI framework)
- Pydantic v2 (data validation)
- Scrapling + BeautifulSoup4 (web scraping)
- SQLite (local storage)
- webtorrent (streaming via mpv)

## Project Conventions

### Code Style
- Use type hints throughout
- Google-style docstrings for public APIs
- Pydantic models for structured data (BaseModel, Field)
- Enums for fixed choices (MediaType)
- Default_factory for mutable defaults in Pydantic models
- No comments unless explaining complex logic

### Architecture Patterns
- Separation: CLI (cli.py), scraping (scraper.py), models (models.py), config (config.py), playback (playback.py), db (db.py)
- Configuration via config.py using pydantic Settings
- Database operations centralized in db.py

### Testing Strategy
- pytest with pytest-cov
- Run `uv run pytest` to execute tests

### Git Workflow
- Conventional commits (not enforced but preferred)
- No specific branching strategy documented

## Domain Context
- gratistorrent.com: Source website for movie/TV torrent links
- webtorrent: Protocol for streaming torrents
- mpv: Media player for playback

## Important Constraints
- Python >=3.12 required
- Requires mpv and webtorrent-cli installed on system

## External Dependencies
- gratistorrent.com: Torrent source (HTML scraping)
- mpv: Media player
- webtorrent-cli: Torrent streaming
