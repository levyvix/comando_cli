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

### Quick install

```bash
curl -fsSL https://raw.githubusercontent.com/levyvix/comando_cli/main/install.sh | bash
```

### Prerequisites

1. **Install Python 3.12+** if not already installed
2. **Install WebTorrent CLI:**
   ```bash
   npm install -g webtorrent
   ```
3. **Install MPV player:**
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
bash install.sh
```

This installs the `com` command globally in your Python environment.

## Usage

### Basic Commands

#### Search for content:
```bash
com search "Breaking Bad"
com search "The Matrix"
```

#### Watch content:
```bash
# Movies
com watch "The Matrix"

# Series (defaults to first episode)
com watch "Breaking Bad"

# Series with specific episodes
com watch "Breaking Bad" -e 2          # Episode 2
com watch "Breaking Bad" -e 2-5        # Episodes 2-5
com watch "Breaking Bad" -e 2-         # Episode 2 onwards
com watch "Breaking Bad" -e -5         # Episodes 1-5
```

#### View watch history:
```bash
com history
```

#### Resume watching:
```bash
com resume
```

### Global Flags

```bash
# Enable verbose output
com --verbose search "Query"
com -v watch "Title"

# Show help
com --help
com search --help
com watch --help
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
- **mpv** - Video player for playback
- **webtorrent-cli** - WebTorrent client used by mpv-webtorrent-hook (`npm install -g webtorrent-cli`)
- **jq** - JSON processor required by mpv-webtorrent-hook
- **xidel** - HTML/XML parser required by mpv-webtorrent-hook (AUR: `yay -S xidel-bin`)
- **mpv-webtorrent-hook** - Enables mpv to open magnet links directly (installed automatically by the CLI)

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
Ensure `webtorrent-cli` is installed globally:
```bash
npm install -g webtorrent-cli
which webtorrent
```

### xidel not found (Arch Linux)
```bash
yay -S xidel-bin
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
