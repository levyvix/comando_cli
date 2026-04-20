"""Tests for quality and language selector module."""

from unittest.mock import patch

import pytest

from comando_cli.models import MediaType, QualityOption, Title
from comando_cli.quality_selector import (
    select_language,
    select_quality,
    select_quality_and_language,
)


@pytest.fixture
def sample_title():
    """Create a sample title with quality options."""
    return Title(
        id="test-movie",
        name="Test Movie",
        media_type=MediaType.MOVIE,
        url="https://example.com/test",
        quality_options=[
            QualityOption(quality="1080p", language="Portuguese", magnet_link="magnet:1"),
            QualityOption(quality="1080p", language="English", magnet_link="magnet:2"),
            QualityOption(quality="720p", language="Portuguese", magnet_link="magnet:3"),
            QualityOption(quality="720p", language="English", magnet_link="magnet:4"),
        ],
    )


@pytest.fixture
def single_quality_title():
    """Create a title with only one quality option."""
    return Title(
        id="test-movie",
        name="Test Movie",
        media_type=MediaType.MOVIE,
        url="https://example.com/test",
        quality_options=[
            QualityOption(quality="1080p", language="Portuguese", magnet_link="magnet:1"),
        ],
    )


@pytest.fixture
def no_quality_title():
    """Create a title with no quality options."""
    return Title(
        id="test-movie",
        name="Test Movie",
        media_type=MediaType.MOVIE,
        url="https://example.com/test",
        quality_options=[],
    )


class TestSelectQuality:
    """Tests for select_quality function."""

    def test_select_quality_returns_selected_option(self, sample_title):
        """Test selecting a quality option."""
        with patch("typer.prompt", return_value=1):
            result = select_quality(sample_title)

            assert result is not None
            assert result.quality == "1080p"

    def test_select_quality_multiple_options(self, sample_title):
        """Test quality selection with multiple options."""
        with patch("typer.prompt", return_value=2):
            result = select_quality(sample_title)

            assert result is not None
            assert result.quality == "720p"

    def test_select_quality_single_option_auto_selects(self, single_quality_title):
        """Test quality selection with only one option auto-selects."""
        with patch("typer.prompt") as mock_prompt:
            result = select_quality(single_quality_title)

            # Should not prompt if only one quality
            mock_prompt.assert_not_called()
            assert result is not None
            assert result.quality == "1080p"

    def test_select_quality_no_options_returns_none(self, no_quality_title):
        """Test quality selection with no options returns None."""
        result = select_quality(no_quality_title)

        assert result is None

    def test_select_quality_invalid_choice_returns_none(self, sample_title):
        """Test quality selection with invalid choice returns None."""
        with patch("typer.prompt", return_value=99):
            result = select_quality(sample_title)

            assert result is None

    def test_select_quality_zero_choice_returns_none(self, sample_title):
        """Test quality selection with zero choice returns None."""
        with patch("typer.prompt", return_value=0):
            result = select_quality(sample_title)

            assert result is None

    def test_select_quality_non_numeric_choice_returns_none(self, sample_title):
        """Test quality selection with non-numeric choice returns None."""
        with patch("typer.prompt", side_effect=ValueError("Invalid")):
            result = select_quality(sample_title)

            assert result is None

    def test_select_quality_keyboard_interrupt_returns_none(self, sample_title):
        """Test quality selection with keyboard interrupt returns None."""
        with patch("typer.prompt", side_effect=KeyboardInterrupt()):
            result = select_quality(sample_title)

            assert result is None

    def test_select_quality_deduplicates_by_quality(self, sample_title):
        """Test quality selection deduplicates options by quality."""
        with patch("typer.prompt", return_value=1):
            result = select_quality(sample_title)

            # Should select first option of 1080p
            assert result.quality == "1080p"
            assert result.language == "Portuguese"  # First occurrence

    def test_select_quality_returns_magnet_link(self, sample_title):
        """Test quality selection returns magnet link."""
        with patch("typer.prompt", return_value=1):
            result = select_quality(sample_title)

            assert result.magnet_link is not None
            assert result.magnet_link.startswith("magnet:")


class TestSelectLanguage:
    """Tests for select_language function."""

    def test_select_language_returns_selected_option(self):
        """Test selecting a language option."""
        options = [
            QualityOption(quality="1080p", language="Portuguese", magnet_link="magnet:1"),
            QualityOption(quality="1080p", language="English", magnet_link="magnet:2"),
        ]

        with patch("typer.prompt", return_value=1):
            result = select_language(options)

            assert result is not None
            assert result.language == "Portuguese"

    def test_select_language_multiple_options(self):
        """Test language selection with multiple options."""
        options = [
            QualityOption(quality="1080p", language="Portuguese", magnet_link="magnet:1"),
            QualityOption(quality="1080p", language="English", magnet_link="magnet:2"),
        ]

        with patch("typer.prompt", return_value=2):
            result = select_language(options)

            assert result is not None
            assert result.language == "English"

    def test_select_language_single_option_auto_selects(self):
        """Test language selection with only one option auto-selects."""
        options = [
            QualityOption(quality="1080p", language="Portuguese", magnet_link="magnet:1"),
        ]

        with patch("typer.prompt") as mock_prompt:
            result = select_language(options)

            # Should not prompt if only one language
            mock_prompt.assert_not_called()
            assert result is not None
            assert result.language == "Portuguese"

    def test_select_language_empty_options_returns_none(self):
        """Test language selection with empty options returns None."""
        result = select_language([])

        assert result is None

    def test_select_language_invalid_choice_returns_none(self):
        """Test language selection with invalid choice returns None."""
        options = [
            QualityOption(quality="1080p", language="Portuguese", magnet_link="magnet:1"),
            QualityOption(quality="1080p", language="English", magnet_link="magnet:2"),
        ]

        with patch("typer.prompt", return_value=99):
            result = select_language(options)

            assert result is None

    def test_select_language_keyboard_interrupt_returns_none(self):
        """Test language selection with keyboard interrupt returns None."""
        options = [
            QualityOption(quality="1080p", language="Portuguese", magnet_link="magnet:1"),
            QualityOption(quality="1080p", language="English", magnet_link="magnet:2"),
        ]

        with patch("typer.prompt", side_effect=KeyboardInterrupt()):
            result = select_language(options)

            assert result is None

    def test_select_language_deduplicates_by_language(self):
        """Test language selection deduplicates options by language."""
        options = [
            QualityOption(quality="1080p", language="Portuguese", magnet_link="magnet:1"),
            QualityOption(quality="1080p", language="Portuguese", magnet_link="magnet:2"),
            QualityOption(quality="1080p", language="English", magnet_link="magnet:3"),
        ]

        with patch("typer.prompt", return_value=1):
            result = select_language(options)

            assert result.language == "Portuguese"
            assert result.magnet_link == "magnet:1"  # First occurrence

    def test_select_language_prefers_dual_audio_as_default(self):
        """Test language prompt defaults to Dual Audio when available."""
        options = [
            QualityOption(quality="1080p", language="Legendado", magnet_link="magnet:1"),
            QualityOption(quality="1080p", language="Dual Audio", magnet_link="magnet:2"),
        ]

        with patch("typer.prompt", return_value=2) as mock_prompt:
            result = select_language(options)

            mock_prompt.assert_called_once_with("Enter choice (number)", type=int, default=2)
            assert result is not None
            assert result.language == "Dual Audio"

    def test_select_language_prefers_dublado_as_default(self):
        """Test language prompt defaults to Dublado when available."""
        options = [
            QualityOption(quality="1080p", language="Legendado", magnet_link="magnet:1"),
            QualityOption(quality="1080p", language="Dublado", magnet_link="magnet:2"),
        ]

        with patch("typer.prompt", return_value=2) as mock_prompt:
            result = select_language(options)

            mock_prompt.assert_called_once_with("Enter choice (number)", type=int, default=2)
            assert result is not None
            assert result.language == "Dublado"


class TestSelectQualityAndLanguage:
    """Tests for select_quality_and_language function."""

    def test_select_quality_and_language_selects_with_fzf(self, sample_title):
        """Test selecting magnet option via fzf output."""
        fzf_output = "2. 1080p | English | Movie/All\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = fzf_output

            result = select_quality_and_language(sample_title)

            assert result is not None
            assert result.quality == "1080p"
            assert result.language == "English"

    def test_select_quality_and_language_fzf_cancel_returns_none(self, sample_title):
        """Test returning None when fzf is cancelled."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""

            result = select_quality_and_language(sample_title)

            assert result is None

    def test_select_quality_and_language_no_options_returns_none(self, no_quality_title):
        """Test with no quality options returns None."""
        result = select_quality_and_language(no_quality_title)

        assert result is None

    def test_select_quality_and_language_single_option_auto_selects(self, single_quality_title):
        """Test with single option auto-selects without fzf."""
        with patch("subprocess.run") as mock_run:
            result = select_quality_and_language(single_quality_title)

            mock_run.assert_not_called()
            assert result is not None
            assert result.quality == "1080p"

    def test_select_quality_and_language_fallback_numbered_selection(self, sample_title):
        """Test fallback to numbered selection when fzf is not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            with patch("typer.prompt", return_value=3):
                result = select_quality_and_language(sample_title)

                assert result is not None
                assert result.quality == "720p"
                assert result.language == "Portuguese"

    def test_select_quality_and_language_returns_magnet_link(self, sample_title):
        """Test final selection includes magnet link."""
        fzf_output = "1. 1080p | Portuguese | Movie/All\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = fzf_output
            result = select_quality_and_language(sample_title)

            assert result.magnet_link is not None
            assert result.magnet_link.startswith("magnet:")

    def test_select_quality_and_language_keeps_all_options(self):
        """Test all options remain selectable, including non-dual."""
        title = Title(
            id="test-movie",
            name="Test Movie",
            media_type=MediaType.MOVIE,
            url="https://example.com/test",
            quality_options=[
                QualityOption(quality="1080p", language="Legendado", magnet_link="magnet:1"),
                QualityOption(quality="1080p", language="Dublado", magnet_link="magnet:2"),
            ],
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "1. 1080p | Legendado | Movie/All\n"
            result = select_quality_and_language(title)

            assert result is not None
            assert result.quality == "1080p"
            assert result.language == "Legendado"

    def test_select_quality_and_language_shows_text_after_torrent(self):
        """Test fzf menu displays raw label text after the TORRENT keyword."""
        title = Title(
            id="avatar",
            name="Avatar",
            media_type=MediaType.MOVIE,
            url="https://example.com/avatar",
            quality_options=[
                QualityOption(
                    quality="1080P",
                    language="Dual Audio",
                    magnet_link="magnet:1",
                    display_name="AVATAR - FOGO E CINZAS DOWNLOAD TORRENT DUBLADO DUAL ÁUDIO 5.1 MKV 1080P",
                ),
                QualityOption(
                    quality="4K",
                    language="Legendado",
                    magnet_link="magnet:2",
                    display_name="AVATAR - FOGO E CINZAS DOWNLOAD TORRENT LEGENDADO 5.1 MP4 2160P ULTRA HD 4K HDR",
                ),
            ],
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "1. DUBLADO DUAL ÁUDIO 5.1 MKV 1080P | Movie/All\n"
            result = select_quality_and_language(title)

            assert result is not None
            assert result.magnet_link == "magnet:1"
            sent_input = mock_run.call_args.kwargs["input"]
            assert "DUBLADO DUAL ÁUDIO 5.1 MKV 1080P | Movie/All" in sent_input
            assert "LEGENDADO 5.1 MP4 2160P ULTRA HD 4K HDR | Movie/All" in sent_input
