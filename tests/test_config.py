"""Tests for configuration module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from comando_cli.config import AppConfig, ensure_directories, get_xdg_dirs, load_config


class TestAppConfig:
    """Tests for AppConfig model."""

    def test_app_config_defaults(self):
        """Test AppConfig uses correct defaults."""
        config = AppConfig()

        home = Path.home()
        assert config.cache_dir == home / ".cache" / "comando-cli"
        assert config.config_dir == home / ".config" / "comando-cli"
        assert config.data_dir == home / ".local" / "share" / "comando-cli"
        assert config.verbose is False
        assert config.max_concurrent_downloads == 2
        assert config.scraper == "gratistorrent"

    def test_app_config_scraper_field(self):
        """Test AppConfig accepts custom scraper value."""
        config = AppConfig(scraper="gratistorrent")
        assert config.scraper == "gratistorrent"

    def test_app_config_custom_values(self):
        """Test AppConfig with custom values."""
        custom_cache = Path("/tmp/cache")
        custom_config = Path("/tmp/config")
        custom_data = Path("/tmp/data")

        config = AppConfig(
            cache_dir=custom_cache,
            config_dir=custom_config,
            data_dir=custom_data,
            verbose=True,
            max_concurrent_downloads=4,
        )

        assert config.cache_dir == custom_cache
        assert config.config_dir == custom_config
        assert config.data_dir == custom_data
        assert config.verbose is True
        assert config.max_concurrent_downloads == 4


class TestGetXdgDirs:
    """Tests for get_xdg_dirs function."""

    def test_get_xdg_dirs_defaults(self):
        """Test get_xdg_dirs uses default paths when env vars not set."""
        with patch.dict(os.environ, {}, clear=True):
            config_dir, cache_dir, data_dir = get_xdg_dirs()

            home = Path.home()
            assert config_dir == home / ".config" / "comando-cli"
            assert cache_dir == home / ".cache" / "comando-cli"
            assert data_dir == home / ".local" / "share" / "comando-cli"

    def test_get_xdg_dirs_with_env_vars(self):
        """Test get_xdg_dirs respects environment variables."""
        with patch.dict(
            os.environ,
            {
                "XDG_CONFIG_HOME": "/etc/xdg",
                "XDG_CACHE_HOME": "/var/cache",
                "XDG_DATA_HOME": "/usr/share",
            },
            clear=True,
        ):
            config_dir, cache_dir, data_dir = get_xdg_dirs()

            assert config_dir == Path("/etc/xdg/comando-cli")
            assert cache_dir == Path("/var/cache/comando-cli")
            assert data_dir == Path("/usr/share/comando-cli")

    def test_get_xdg_dirs_partial_env_vars(self):
        """Test get_xdg_dirs with some env vars set."""
        with patch.dict(
            os.environ,
            {"XDG_CONFIG_HOME": "/custom/config"},
            clear=True,
        ):
            config_dir, cache_dir, data_dir = get_xdg_dirs()

            assert config_dir == Path("/custom/config/comando-cli")
            home = Path.home()
            assert cache_dir == home / ".cache" / "comando-cli"
            assert data_dir == home / ".local" / "share" / "comando-cli"


class TestEnsureDirectories:
    """Tests for ensure_directories function."""

    def test_ensure_directories_creates_dirs(self):
        """Test ensure_directories creates all required directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(
                os.environ,
                {
                    "XDG_CONFIG_HOME": tmpdir,
                    "XDG_CACHE_HOME": tmpdir,
                    "XDG_DATA_HOME": tmpdir,
                },
                clear=True,
            ):
                config = ensure_directories()

                assert config.config_dir.exists()
                assert config.cache_dir.exists()
                assert config.data_dir.exists()

    def test_ensure_directories_returns_app_config(self):
        """Test ensure_directories returns AppConfig instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(
                os.environ,
                {
                    "XDG_CONFIG_HOME": tmpdir,
                    "XDG_CACHE_HOME": tmpdir,
                    "XDG_DATA_HOME": tmpdir,
                },
                clear=True,
            ):
                config = ensure_directories()

                assert isinstance(config, AppConfig)
                assert config.verbose is False
                assert config.max_concurrent_downloads == 2

    def test_ensure_directories_idempotent(self):
        """Test ensure_directories is idempotent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(
                os.environ,
                {
                    "XDG_CONFIG_HOME": tmpdir,
                    "XDG_CACHE_HOME": tmpdir,
                    "XDG_DATA_HOME": tmpdir,
                },
                clear=True,
            ):
                config1 = ensure_directories()
                config2 = ensure_directories()

                assert config1.config_dir == config2.config_dir
                assert config1.cache_dir == config2.cache_dir
                assert config1.data_dir == config2.data_dir


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_no_file_returns_defaults(self):
        """Test load_config returns defaults when no config file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            with patch.dict(
                os.environ,
                {
                    "XDG_CONFIG_HOME": tmpdir,
                    "XDG_CACHE_HOME": tmpdir,
                    "XDG_DATA_HOME": tmpdir,
                },
                clear=True,
            ):
                config = load_config(config_dir)

                assert isinstance(config, AppConfig)
                assert config.verbose is False
                assert config.max_concurrent_downloads == 2

    def test_load_config_from_file(self):
        """Test load_config loads from TOML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_file = config_dir / "config.toml"

            # Write test config
            config_file.write_text(
                """
[app]
verbose = true
max_concurrent_downloads = 4
"""
            )

            with patch.dict(
                os.environ,
                {
                    "XDG_CONFIG_HOME": tmpdir,
                    "XDG_CACHE_HOME": tmpdir,
                    "XDG_DATA_HOME": tmpdir,
                },
                clear=True,
            ):
                config = load_config(config_dir)

                assert config.verbose is True
                assert config.max_concurrent_downloads == 4

    def test_load_config_partial_override(self):
        """Test load_config with partial config overrides defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_file = config_dir / "config.toml"

            # Write partial config
            config_file.write_text(
                """
[app]
verbose = true
"""
            )

            with patch.dict(
                os.environ,
                {
                    "XDG_CONFIG_HOME": tmpdir,
                    "XDG_CACHE_HOME": tmpdir,
                    "XDG_DATA_HOME": tmpdir,
                },
                clear=True,
            ):
                config = load_config(config_dir)

                assert config.verbose is True
                assert config.max_concurrent_downloads == 2  # Default

    def test_load_config_invalid_file_returns_defaults(self):
        """Test load_config returns defaults on invalid TOML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_file = config_dir / "config.toml"

            # Write invalid TOML
            config_file.write_text("invalid toml content [[[")

            with patch.dict(
                os.environ,
                {
                    "XDG_CONFIG_HOME": tmpdir,
                    "XDG_CACHE_HOME": tmpdir,
                    "XDG_DATA_HOME": tmpdir,
                },
                clear=True,
            ):
                config = load_config(config_dir)

                assert isinstance(config, AppConfig)
                assert config.verbose is False

    def test_load_config_creates_directories(self):
        """Test load_config creates directories when loading config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_file = config_dir / "config.toml"

            config_file.write_text("[app]\nverbose = true\n")

            with patch.dict(
                os.environ,
                {
                    "XDG_CONFIG_HOME": tmpdir,
                    "XDG_CACHE_HOME": tmpdir,
                    "XDG_DATA_HOME": tmpdir,
                },
                clear=True,
            ):
                config = load_config(config_dir)

                assert config.config_dir.exists()
                assert config.cache_dir.exists()
                assert config.data_dir.exists()

    def test_load_config_with_custom_paths(self):
        """Test load_config respects custom paths in TOML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_file = config_dir / "config.toml"

            custom_cache = Path(tmpdir) / "my_cache"
            config_file.write_text(
                f"""
[app]
cache_dir = "{custom_cache}"
verbose = true
"""
            )

            with patch.dict(
                os.environ,
                {
                    "XDG_CONFIG_HOME": tmpdir,
                    "XDG_CACHE_HOME": tmpdir,
                    "XDG_DATA_HOME": tmpdir,
                },
                clear=True,
            ):
                config = load_config(config_dir)

                assert config.cache_dir == custom_cache
                assert config.verbose is True

    def test_load_config_empty_app_section(self):
        """Test load_config with empty [app] section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_file = config_dir / "config.toml"

            # TOML with empty app section
            config_file.write_text("[other]\nkey = 'value'\n")

            with patch.dict(
                os.environ,
                {
                    "XDG_CONFIG_HOME": tmpdir,
                    "XDG_CACHE_HOME": tmpdir,
                    "XDG_DATA_HOME": tmpdir,
                },
                clear=True,
            ):
                config = load_config(config_dir)

                # Should use defaults when [app] is missing
                assert config.verbose is False
                assert config.max_concurrent_downloads == 2
