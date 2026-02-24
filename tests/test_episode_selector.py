"""Tests for episode selector module."""

import pytest

from comando_cli.episode_selector import (
    EpisodeSelectorError,
    format_episode_list,
    parse_episode_syntax,
    validate_episodes,
)


class TestParseEpisodeSyntax:
    """Tests for parse_episode_syntax function."""

    def test_single_episode(self):
        """Test parsing single episode."""
        result = parse_episode_syntax("2", 10)
        assert result.episodes == [2]
        assert result.original_input == "2"

    def test_episode_range(self):
        """Test parsing episode range."""
        result = parse_episode_syntax("2-5", 10)
        assert result.episodes == [2, 3, 4, 5]

    def test_open_range_to_end(self):
        """Test parsing range to end of series."""
        result = parse_episode_syntax("2-", 10)
        assert result.episodes == [2, 3, 4, 5, 6, 7, 8, 9, 10]

    def test_prefix_range_from_start(self):
        """Test parsing range from start."""
        result = parse_episode_syntax("-5", 10)
        assert result.episodes == [1, 2, 3, 4, 5]

    def test_single_episode_as_one(self):
        """Test single episode when total is 1."""
        result = parse_episode_syntax("1", 1)
        assert result.episodes == [1]

    def test_entire_series(self):
        """Test selecting entire series."""
        result = parse_episode_syntax("-10", 10)
        assert result.episodes == list(range(1, 11))

    def test_invalid_empty_syntax(self):
        """Test empty syntax raises error."""
        with pytest.raises(EpisodeSelectorError, match="cannot be empty"):
            parse_episode_syntax("", 10)

    def test_invalid_total_episodes(self):
        """Test invalid total episode count."""
        with pytest.raises(EpisodeSelectorError, match="Invalid total"):
            parse_episode_syntax("1", 0)

    def test_episode_out_of_range_single(self):
        """Test single episode out of range."""
        with pytest.raises(EpisodeSelectorError, match="out of range"):
            parse_episode_syntax("15", 10)

    def test_episode_below_range_single(self):
        """Test single episode below range."""
        with pytest.raises(EpisodeSelectorError, match="out of range"):
            parse_episode_syntax("0", 10)

    def test_range_start_out_of_range(self):
        """Test range start out of range."""
        with pytest.raises(EpisodeSelectorError, match="out of range"):
            parse_episode_syntax("15-20", 10)

    def test_range_end_before_start(self):
        """Test range end before start."""
        with pytest.raises(EpisodeSelectorError, match="out of range"):
            parse_episode_syntax("8-5", 10)

    def test_range_end_out_of_range(self):
        """Test range end out of range."""
        with pytest.raises(EpisodeSelectorError, match="out of range"):
            parse_episode_syntax("5-15", 10)

    def test_invalid_syntax_double_dash(self):
        """Test invalid syntax with double dash."""
        with pytest.raises(EpisodeSelectorError, match="out of range"):
            parse_episode_syntax("--5", 10)

    def test_whitespace_handling(self):
        """Test syntax with whitespace."""
        result = parse_episode_syntax("  2  ", 10)
        assert result.episodes == [2]

    def test_non_numeric_raises_error(self):
        """Test non-numeric input raises error."""
        with pytest.raises((ValueError, EpisodeSelectorError)):
            parse_episode_syntax("abc", 10)


class TestValidateEpisodes:
    """Tests for validate_episodes function."""

    def test_valid_single_episode(self):
        """Test validation of single valid episode."""
        assert validate_episodes([2], 10) is True

    def test_valid_episode_range(self):
        """Test validation of valid episode range."""
        assert validate_episodes([1, 2, 3, 4, 5], 10) is True

    def test_empty_list(self):
        """Test validation of empty list."""
        assert validate_episodes([], 10) is False

    def test_episode_out_of_range(self):
        """Test validation with episode out of range."""
        assert validate_episodes([1, 2, 15], 10) is False

    def test_episode_zero(self):
        """Test validation with episode 0."""
        assert validate_episodes([0, 1, 2], 10) is False

    def test_negative_episode(self):
        """Test validation with negative episode."""
        assert validate_episodes([-1, 1, 2], 10) is False

    def test_all_episodes(self):
        """Test validation of all episodes."""
        assert validate_episodes(list(range(1, 11)), 10) is True


class TestFormatEpisodeList:
    """Tests for format_episode_list function."""

    def test_single_episode(self):
        """Test formatting single episode."""
        assert format_episode_list([2]) == "2"

    def test_consecutive_episodes(self):
        """Test formatting consecutive episodes."""
        assert format_episode_list([1, 2, 3, 4, 5]) == "1-5"

    def test_mixed_consecutive_and_single(self):
        """Test formatting mixed consecutive and single episodes."""
        result = format_episode_list([1, 2, 3, 5, 7, 8, 9])
        assert result == "1-3, 5, 7-9"

    def test_all_single_episodes(self):
        """Test formatting non-consecutive episodes."""
        assert format_episode_list([1, 3, 5, 7]) == "1, 3, 5, 7"

    def test_empty_list(self):
        """Test formatting empty list."""
        assert format_episode_list([]) == ""

    def test_two_consecutive(self):
        """Test formatting two consecutive episodes."""
        assert format_episode_list([1, 2]) == "1-2"

    def test_large_range(self):
        """Test formatting large episode range."""
        assert format_episode_list(list(range(1, 101))) == "1-100"
