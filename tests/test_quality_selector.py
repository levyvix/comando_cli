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


class TestSelectQualityAndLanguage:
    """Tests for select_quality_and_language function."""

    def test_select_quality_and_language_full_flow(self, sample_title):
        """Test full quality and language selection flow."""
        with patch("typer.prompt", side_effect=[1, 1]):  # Quality 1 (1080p), Language 1 (Portuguese)
            result = select_quality_and_language(sample_title)

            assert result is not None
            assert result.quality == "1080p"
            assert result.language == "Portuguese"

    def test_select_quality_and_language_different_selections(self, sample_title):
        """Test selecting different quality and language."""
        with patch("typer.prompt", side_effect=[2, 2]):  # Quality 2 (720p), Language 2 (English)
            result = select_quality_and_language(sample_title)

            assert result is not None
            assert result.quality == "720p"
            assert result.language == "English"

    def test_select_quality_and_language_quality_cancelled_returns_none(self, sample_title):
        """Test cancelling at quality step returns None."""
        with patch("typer.prompt", side_effect=KeyboardInterrupt()):
            result = select_quality_and_language(sample_title)

            assert result is None

    def test_select_quality_and_language_language_cancelled_returns_none(self, sample_title):
        """Test cancelling at language step returns None."""
        # Quality selection succeeds, language selection fails
        with patch("typer.prompt", side_effect=[1, KeyboardInterrupt()]):
            result = select_quality_and_language(sample_title)

            assert result is None

    def test_select_quality_and_language_filters_by_quality(self, sample_title):
        """Test language selection is filtered by selected quality."""
        # Select 1080p quality, then first language option
        with patch("typer.prompt", side_effect=[1, 1]):
            result = select_quality_and_language(sample_title)

            # Should filter to only 1080p options before language selection
            assert result.quality == "1080p"

    def test_select_quality_and_language_no_options_returns_none(self, no_quality_title):
        """Test with no quality options returns None."""
        result = select_quality_and_language(no_quality_title)

        assert result is None

    def test_select_quality_and_language_single_option_both_steps(self, single_quality_title):
        """Test with single option skips both prompts."""
        with patch("typer.prompt") as mock_prompt:
            result = select_quality_and_language(single_quality_title)

            # Should not prompt at all - only one quality and one language
            mock_prompt.assert_not_called()
            assert result is not None
            assert result.quality == "1080p"

    def test_select_quality_and_language_returns_magnet_link(self, sample_title):
        """Test final selection includes magnet link."""
        with patch("typer.prompt", side_effect=[1, 1]):
            result = select_quality_and_language(sample_title)

            assert result.magnet_link is not None
            assert result.magnet_link.startswith("magnet:")
