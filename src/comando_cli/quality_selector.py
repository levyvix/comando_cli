"""Quality and language selection menus."""

import subprocess
from typing import Optional

import typer

from .models import QualityOption, Title


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

    if len(language_list) == 1:
        typer.echo(f"✓ Language: {language_list[0]}")
        return languages[language_list[0]]

    typer.echo("\n🗣️  Select language:")
    for i, language in enumerate(language_list, 1):
        typer.echo(f"  {i}. {language}")

    try:
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
    """Full quality and language selection flow.

    Args:
        title: Title object with quality options
        episode: Episode number to filter by (for series)

    Returns:
        Selected QualityOption or None if cancelled
    """
    # Filter by episode if specified
    quality_options = title.quality_options
    if episode is not None:
        quality_options = [opt for opt in quality_options if opt.episode == episode or opt.episode is None]
    
    if not quality_options:
        return None
    
    # Create a temporary title with filtered options for selection
    filtered_title = title
    filtered_title.quality_options = quality_options

    # Step 1: Quality selection
    quality_option = select_quality(filtered_title)
    if not quality_option:
        return None

    # Filter options by selected quality
    same_quality_options = [
        opt for opt in quality_options if opt.quality == quality_option.quality
    ]

    # Step 2: Language selection
    language_option = select_language(same_quality_options)

    return language_option


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
