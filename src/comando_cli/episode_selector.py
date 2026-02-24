"""Episode selection with flexible syntax parsing."""

from dataclasses import dataclass


@dataclass
class EpisodeRange:
    """Represents an episode range selection."""

    episodes: list[int]
    original_input: str


class EpisodeSelectorError(Exception):
    """Episode selector error."""

    pass


def parse_episode_syntax(syntax: str, total_episodes: int) -> EpisodeRange:
    """Parse episode selection syntax.

    Supports:
    - Single episode: "2" → [2]
    - Range: "2-5" → [2, 3, 4, 5]
    - Open range (to end): "2-" → [2, 3, ..., total_episodes]
    - Prefix range (from start): "-5" → [1, 2, 3, 4, 5]

    Args:
        syntax: Episode selection string
        total_episodes: Total number of episodes available

    Returns:
        EpisodeRange with parsed episodes

    Raises:
        EpisodeSelectorError: If syntax is invalid or episodes out of range
    """
    syntax = syntax.strip()

    if not syntax:
        raise EpisodeSelectorError("Episode syntax cannot be empty")

    if total_episodes <= 0:
        raise EpisodeSelectorError("Invalid total episode count")

    # Single episode: "2"
    if syntax.isdigit():
        ep = int(syntax)
        if ep < 1 or ep > total_episodes:
            raise EpisodeSelectorError(f"Episode {ep} out of range (1-{total_episodes})")
        return EpisodeRange(episodes=[ep], original_input=syntax)

    # Range formats: "2-5", "2-", "-5"
    if "-" in syntax:
        parts = syntax.split("-", 1)

        # "2-5" or "2-"
        if parts[0]:
            start = int(parts[0])
            if start < 1 or start > total_episodes:
                raise EpisodeSelectorError(
                    f"Start episode {start} out of range (1-{total_episodes})"
                )

            # "2-5"
            if parts[1]:
                end = int(parts[1])
                if end < start or end > total_episodes:
                    raise EpisodeSelectorError(
                        f"End episode {end} out of range ({start}-{total_episodes})"
                    )
                episodes = list(range(start, end + 1))
            else:
                # "2-" (to end)
                episodes = list(range(start, total_episodes + 1))

        else:
            # "-5" (from start)
            if not parts[1]:
                raise EpisodeSelectorError("Invalid episode syntax")
            end = int(parts[1])
            if end < 1 or end > total_episodes:
                raise EpisodeSelectorError(
                    f"End episode {end} out of range (1-{total_episodes})"
                )
            episodes = list(range(1, end + 1))

        return EpisodeRange(episodes=episodes, original_input=syntax)

    raise EpisodeSelectorError(f"Invalid episode syntax: {syntax}")


def validate_episodes(episodes: list[int], total_episodes: int) -> bool:
    """Validate that all episodes exist.

    Args:
        episodes: List of episode numbers
        total_episodes: Total number of episodes

    Returns:
        True if all episodes are valid
    """
    if not episodes:
        return False

    for ep in episodes:
        if ep < 1 or ep > total_episodes:
            return False

    return True


def format_episode_list(episodes: list[int]) -> str:
    """Format episode list for display.

    Args:
        episodes: List of episode numbers

    Returns:
        Formatted string (e.g., "1-5, 7, 9-10")
    """
    if not episodes:
        return ""

    # Group consecutive episodes into ranges
    ranges = []
    start = episodes[0]
    end = episodes[0]

    for ep in episodes[1:]:
        if ep == end + 1:
            end = ep
        else:
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            start = ep
            end = ep

    # Add final range
    if start == end:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}-{end}")

    return ", ".join(ranges)
