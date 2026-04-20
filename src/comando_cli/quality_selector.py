"""Quality and language selection menus."""

import re
import subprocess
import unicodedata
from typing import Optional

import typer

from .models import QualityOption, Title


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

    try:
        proc = subprocess.run(
            ["fzf", "--prompt=Select magnet> ", "--height=50%", "--reverse"],
            input="\n".join(labels),
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            selected_label = proc.stdout.strip()
            return label_to_option.get(selected_label)
        return None
    except FileNotFoundError:
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
    input_text = "\n".join(labels)

    try:
        proc = subprocess.run(
            ["fzf", "--prompt=Select title> ", "--height=40%", "--reverse"],
            input=input_text,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return None
        selected_label = proc.stdout.strip()
        for i, label in enumerate(labels):
            if label == selected_label:
                return results[i]
    except FileNotFoundError:
        # fzf not available, fallback to numbered list
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
