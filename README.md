# Comando CLI

Stream movies and TV series from gratistorrent.com directly from your terminal.

## Features

- 🔍 **Search** - Find movies and TV series on gratistorrent.com
- ▶️ **Watch** - Stream content directly using webtorrent
- 📺 **Watch History** - Track your watched content
- ⏸️ **Resume** - Continue from where you left off
- 🎯 **Episode Selection** - Choose specific episodes for series with flexible syntax (e.g., `2`, `2-5`, `2-`, `-5`)
- 🎬 **Quality Selection** - Choose quality and language for streaming
- 🌐 **Direct Torrenting** - Stream via WebTorrent with MPV integration

## System Requirements

- **Python:** 3.12 or higher
- **OS:** Linux, macOS, or WSL
- **Additional:** WebTorrent CLI (`webtorrent`) and MPV player

## Installation

### Prerequisites

1. **Install Python 3.12+** if not already installed
2. **Install UV** (Python package manager):
   ```bash
   pip install uv
   ```
3. **Install WebTorrent CLI:**
   ```bash
   npm install -g webtorrent
   ```
4. **Install MPV player:**
   - **Ubuntu/Debian:**
     ```bash
     sudo apt-get install mpv
     ```
   - **macOS:**
     ```bash
     brew install mpv
     ```
   - **Arch:**
     ```bash
     sudo pacman -S mpv
     ```

### Install Comando CLI

Clone and install the project:

```bash
cd ~/path/to/comando_cli
uv pip install -e .
```

This installs the `com` command globally in your Python environment.

## Usage

### Basic Commands

#### Search for content:
```bash
uv run com search "Breaking Bad"
com search "The Matrix"
```

#### Watch content:
```bash
# Movies
uv run com watch "The Matrix"

# Series (defaults to first episode)
uv run com watch "Breaking Bad"

# Series with specific episodes
uv run com watch "Breaking Bad" -e 2          # Episode 2
uv run com watch "Breaking Bad" -e 2-5        # Episodes 2-5
uv run com watch "Breaking Bad" -e 2-         # Episode 2 onwards
uv run com watch "Breaking Bad" -e -5         # Episodes 1-5
```

#### View watch history:
```bash
uv run com history
```

#### Resume watching:
```bash
uv run com resume
```

### Global Flags

```bash
# Enable verbose output
uv run com --verbose search "Query"
uv run com -v watch "Title"

# Show help
uv run com --help
uv run com search --help
uv run com watch --help
```

## Running Without `uv run`

### Option 1: Add to PATH
```bash
export PATH="$PWD/.venv/bin:$PATH"
com search "Movie"
com watch "Title"
```

### Option 2: Create a symlink
```bash
sudo ln -s $(pwd)/.venv/bin/com /usr/local/bin/com
com search "Movie"
```

### Option 3: Direct venv execution
```bash
.venv/bin/com search "Movie"
```

## Dependencies

### Core Dependencies
- **typer** (≥0.24.1) - CLI framework for creating command-line interfaces
- **beautifulsoup4** (≥4.14.3) - HTML parsing for web scraping
- **pydantic** (≥2.12.5) - Data validation and serialization
- **scrapling** (≥0.4) - Advanced web scraping with intelligent element selection

### External Tools
- **webtorrent** - WebTorrent client for streaming torrents
- **mpv** - Video player for playback

### Development Dependencies
- **pytest** (≥9.0.2) - Testing framework
- **pytest-cov** (≥7.0.0) - Code coverage measurement

## Configuration

The application stores its configuration and data in:
- **Config Directory:** `~/.config/comando_cli/`
- **Data Directory:** `~/.local/share/comando_cli/`
- **Watch History:** `~/.local/share/comando_cli/history.db`

## Development

### Run tests:
```bash
uv run pytest
uv run pytest --cov=src
```

### Install development dependencies:
```bash
uv pip install -e ".[dev]"
```

## Troubleshooting

### WebTorrent not found
Ensure `webtorrent` is installed globally:
```bash
npm install -g webtorrent
which webtorrent
```

### MPV not found
Install MPV for your system (see Installation section)

### Python version mismatch
Verify you're using Python 3.12+:
```bash
python --version
```

## Project Structure

```
comando_cli/
├── src/comando_cli/
│   ├── cli.py              # Main CLI commands
│   ├── scraper.py          # Gratistorrent web scraper
│   ├── models.py           # Data models (Pydantic)
│   ├── db.py               # Watch history database
│   ├── playback.py         # Torrent playback logic
│   ├── quality_selector.py # Quality/language selection
│   ├── episode_selector.py # Episode parsing logic
│   └── config.py           # Configuration management
├── tests/                  # Test suite
├── pyproject.toml          # Project metadata and dependencies
└── README.md              # This file
```

## License

See project LICENSE file for details.

## Contributing

Contributions are welcome! Please ensure:
- Tests pass: `uv run pytest`
- Code coverage: ≥80%
- Follow existing code patterns and style
