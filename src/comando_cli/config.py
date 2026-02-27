"""Configuration management with XDG Base Directory support."""

import os
import tomllib
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Application configuration."""

    cache_dir: Path = Field(
        default_factory=lambda: Path.home() / ".cache" / "comando-cli"
    )
    config_dir: Path = Field(
        default_factory=lambda: Path.home() / ".config" / "comando-cli"
    )
    data_dir: Path = Field(
        default_factory=lambda: Path.home() / ".local" / "share" / "comando-cli"
    )
    download_dir: Optional[Path] = Field(default=None)
    verbose: bool = False
    max_concurrent_downloads: int = 2
    # scraper: str = "gratistorrent"  # or comando_la
    scraper: str = "comando_la"


def get_xdg_dirs() -> tuple[Path, Path, Path]:
    """Get XDG Base Directory paths for comando-cli.

    Returns:
        Tuple of (config_dir, cache_dir, data_dir)
    """
    config_dir = (
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "comando-cli"
    )
    cache_dir = (
        Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "comando-cli"
    )
    data_dir = (
        Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        / "comando-cli"
    )

    return config_dir, cache_dir, data_dir


def ensure_directories() -> AppConfig:
    """Ensure all required directories exist and return config.

    Returns:
        AppConfig with verified paths
    """
    config_dir, cache_dir, data_dir = get_xdg_dirs()

    config_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    return AppConfig(
        config_dir=config_dir,
        cache_dir=cache_dir,
        data_dir=data_dir,
    )


def load_config(config_dir: Path) -> AppConfig:
    """Load configuration from TOML file or return defaults.

    Args:
        config_dir: Directory containing config.toml

    Returns:
        AppConfig instance
    """
    config_file = config_dir / "config.toml"

    if not config_file.exists():
        return ensure_directories()

    try:
        with open(config_file, "rb") as f:
            config_dict = tomllib.load(f)
        return AppConfig(**config_dict.get("app", {}))
    except Exception:
        return ensure_directories()
