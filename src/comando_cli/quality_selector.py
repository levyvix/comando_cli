"""Quality and language selection menus."""

import re
import unicodedata
from typing import Optional

import typer

from comando_cli.fuzzy import select_with_fzf
from comando_cli.models import QualityOption, Title, TorrentFile


def _normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.upper()


def _is_dual_audio(language: str) -> bool:
    return "DUAL" in _normalize_text(language)


def _is_dual_or_dubbed(language: str) -> bool:
    normalized = _normalize_text(language)
    return (
        "DUAL" in normalized
        or "DUBLADO" in normalized
        or "DUBBED" in normalized
    )


def select_quality(title: Title) -> Optional[QualityOption]:
    """Interactive menu to select quality.

    Args:
        title: Title object with quality options

    Returns:
        Selected QualityOption or None if cancelled
    """
    if not title.quality_options:
        typer.echo("❌ No quality options available")
        return None

    # Group options by quality
    qualities = {}
    for option in title.quality_options:
        if option.quality not in qualities:
            qualities[option.quality] = option

    quality_list = list(qualities.keys())

    if len(quality_list) == 1:
        typer.echo(f"✓ Quality: {quality_list[0]}")
        return qualities[quality_list[0]]

    typer.echo("\n📺 Select quality:")
    for i, quality in enumerate(quality_list, 1):
        typer.echo(f"  {i}. {quality}")

    try:
        choice = typer.prompt("Enter choice (number)", type=int)
        if choice < 1 or choice > len(quality_list):
            typer.echo("Invalid choice")
            return None

        selected_quality = quality_list[choice - 1]
        return qualities[selected_quality]

    except (ValueError, KeyboardInterrupt):
        typer.echo("Cancelled")
        return None


def select_language(options: list[QualityOption]) -> Optional[QualityOption]:
    """Interactive menu to select language from quality-filtered options.

    Args:
        options: List of quality options with language variants

    Returns:
        Selected QualityOption or None if cancelled
    """
    if not options:
        typer.echo("❌ No language options available")
        return None

    # Group by language
    languages = {}
    for option in options:
        if option.language not in languages:
            languages[option.language] = option

    language_list = list(languages.keys())

    preferred_index = next(
        (idx for idx, language in enumerate(language_list) if _is_dual_or_dubbed(language)),
        None,
    )

    if len(language_list) == 1:
        typer.echo(f"✓ Language: {language_list[0]}")
        return languages[language_list[0]]

    typer.echo("\n🗣️  Select language:")
    for i, language in enumerate(language_list, 1):
        typer.echo(f"  {i}. {language}")

    try:
        if preferred_index is not None:
            default_choice = preferred_index + 1
            choice = typer.prompt(
                "Enter choice (number)",
                type=int,
                default=default_choice,
            )
        else:
            choice = typer.prompt("Enter choice (number)", type=int)

        if choice < 1 or choice > len(language_list):
            typer.echo("Invalid choice")
            return None

        selected_language = language_list[choice - 1]
        return languages[selected_language]

    except (ValueError, KeyboardInterrupt):
        typer.echo("Cancelled")
        return None


def select_quality_and_language(title: Title, episode: Optional[int] = None) -> Optional[QualityOption]:
    """Select a magnet option from all available variants.

    Args:
        title: Title object with quality options
        episode: Episode number to filter by (for series)

    Returns:
        Selected QualityOption or None if cancelled
    """
    # Filter by episode if specified
    quality_options = title.quality_options
    if episode is not None:
        quality_options = [
            opt for opt in quality_options
            if opt.episode is None
            or opt.episode <= episode <= (opt.episode_end or opt.episode)
        ]

    if not quality_options:
        if episode is not None:
            typer.echo(f"❌ No quality options available for episode {episode}")
        else:
            typer.echo("❌ No quality options available")
        return None

    if len(quality_options) == 1:
        selected = quality_options[0]
        typer.echo(f"✓ Magnet: {selected.quality} {selected.language}")
        return selected

    labels: list[str] = []
    label_to_option: dict[str, QualityOption] = {}

    def _menu_text(option: QualityOption) -> str:
        raw = (option.display_name or "").strip()
        if raw:
            match = re.search(r"\bTORRENT\b\s*(.+)", raw, flags=re.IGNORECASE)
            if match and match.group(1).strip():
                return match.group(1).strip()
            return raw
        return f"{option.quality} | {option.language}"

    for idx, option in enumerate(quality_options, 1):
        if option.episode is not None:
            episode_text = (
                f"E{option.episode:02d}-E{option.episode_end:02d}"
                if option.episode_end is not None
                else f"E{option.episode:02d}"
            )
        else:
            episode_text = "Movie/All"

        label = f"{idx}. {_menu_text(option)} | {episode_text}"
        labels.append(label)
        label_to_option[label] = option

    selected_label = select_with_fzf(labels, prompt="Select magnet> ", height="50%")
    if selected_label is not None:
        return label_to_option.get(selected_label)

    typer.echo("\n🧲 Select magnet:")
    for idx, label in enumerate(labels, 1):
        typer.echo(f"  {idx}. {label}")
    try:
        choice = typer.prompt("Enter choice (number)", type=int)
        if 1 <= choice <= len(quality_options):
            return quality_options[choice - 1]
    except (ValueError, KeyboardInterrupt):
        typer.echo("Cancelled")
        return None

    return None


def select_title(results: list[Title]) -> Optional[Title]:
    """Interactive fzf selection from search results.

    Args:
        results: List of Title objects from search

    Returns:
        Selected Title or None if cancelled
    """
    if not results:
        return None

    if len(results) == 1:
        return results[0]

    labels = [f"{t.name} ({t.media_type.value})" for t in results]
    selected_label = select_with_fzf(labels, prompt="Select title> ", height="40%")
    if selected_label is not None:
        for i, label in enumerate(labels):
            if label == selected_label:
                return results[i]

    # fzf not available, cancelled, or invalid selection: fallback to numbered list
    typer.echo("\n🔍 Select a title:")
    for i, label in enumerate(labels, 1):
        typer.echo(f"  {i}. {label}")
    try:
        choice = typer.prompt("Enter choice (number)", type=int)
        if 1 <= choice <= len(results):
            return results[choice - 1]
    except (ValueError, KeyboardInterrupt):
        pass

    return None


def select_torrent_file(files: list[TorrentFile]) -> Optional[TorrentFile]:
    """Interactive selection for the file to start playback from."""
    if not files:
        return None
    if len(files) == 1:
        return files[0]

    labels: list[str] = []
    label_to_file: dict[str, TorrentFile] = {}
    for i, torrent_file in enumerate(files, 1):
        ep = f"E{torrent_file.episode:02d}" if torrent_file.episode is not None else "--"
        filename = torrent_file.path.split("/")[-1]
        label = f"{i}. {ep} | {filename}"
        labels.append(label)
        label_to_file[label] = torrent_file

    selected_label = select_with_fzf(labels, prompt="Select torrent/file> ", height="50%")
    if selected_label is not None:
        return label_to_file.get(selected_label)

    typer.echo("\n🧲 Select torrent/file:")
    for idx, label in enumerate(labels, 1):
        typer.echo(f"  {idx}. {label}")
    try:
        choice = typer.prompt("Enter choice (number)", type=int)
        if 1 <= choice <= len(files):
            return files[choice - 1]
    except (ValueError, KeyboardInterrupt):
        typer.echo("Cancelled")
        return None

    return None


def select_episode_magnet(options: list[QualityOption]) -> Optional[QualityOption]:
    """Interactive selection for series episode magnets."""
    if not options:
        return None
    if len(options) == 1:
        return options[0]

    sorted_options = sorted(
        options,
        key=lambda opt: (
            opt.episode if opt.episode is not None else 9999,
            opt.episode_end if opt.episode_end is not None else 9999,
            opt.display_name or "",
        ),
    )

    labels: list[str] = []
    label_to_option: dict[str, QualityOption] = {}
    for idx, option in enumerate(sorted_options, 1):
        if option.episode is not None and option.episode_end is not None:
            ep_text = f"E{option.episode:02d}-E{option.episode_end:02d}"
        elif option.episode is not None:
            ep_text = f"E{option.episode:02d}"
        else:
            ep_text = "ALL"
        name = (option.display_name or f"{option.quality} {option.language}").strip()
        label = f"{idx}. {ep_text} | {name}"
        labels.append(label)
        label_to_option[label] = option

    selected_label = select_with_fzf(labels, prompt="Select episode/torrent> ", height="50%")
    if selected_label is not None:
        return label_to_option.get(selected_label)

    typer.echo("\n🧲 Select episode/torrent:")
    for idx, label in enumerate(labels, 1):
        typer.echo(f"  {idx}. {label}")
    try:
        choice = typer.prompt("Enter choice (number)", type=int)
        if 1 <= choice <= len(sorted_options):
            return sorted_options[choice - 1]
    except (ValueError, KeyboardInterrupt):
        typer.echo("Cancelled")
        return None

    return None
