# Change: Add Streaming CLI for Movies and TV Series

## Why
Users want a convenient command-line interface to search for, discover, and stream movies and TV series from gratistorrent.com. Currently there's no way to access this content programmatically through a CLI, requiring manual browser interaction. A CLI tool provides:
- Fast text-based search with fuzzy matching (fzf)
- Programmatic torrent streaming with webtorrent + mpv
- Episode selection for series with flexible syntax
- Watch history tracking for seamless continuity

## What Changes
- **NEW**: Core search capability against gratistorrent.com with Cloudflare handling
- **NEW**: Movie/series content discovery and metadata scraping
- **NEW**: Episode selection system with flexible syntax (-e 2, -e 2-5, -e 2-, -e -5)
- **NEW**: Playback engine combining webtorrent + mpv
- **NEW**: Quality/language selector menu
- **NEW**: Local watch history database tracking current episode

## Impact
- **Affected specs**: search, episode-selection, playback, watch-history
- **Affected code**: New capabilities in main.py and supporting modules
- **External dependencies**: Scrapling (web scraping), webtorrent (torrent streaming), mpv (video player), fzf (fuzzy finder)
- **Storage**: ~/.config/comando-cli/ for cache, history, and configuration

## Architecture Highlights
- Modular design: separate modules for scraping, episode selection, playback, history
- Streaming-first: webtorrent downloads to temp directory, mpv plays from there
- XDG Base Directory compliance: uses ~/.config/ and ~/.cache/
- Event-driven playback: watch history updates when playback completes
