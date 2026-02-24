"""Quality and language selection menus."""

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


def select_quality_and_language(title: Title) -> Optional[QualityOption]:
    """Full quality and language selection flow.

    Args:
        title: Title object with quality options

    Returns:
        Selected QualityOption or None if cancelled
    """
    # Step 1: Quality selection
    quality_option = select_quality(title)
    if not quality_option:
        return None

    # Filter options by selected quality
    same_quality_options = [
        opt for opt in title.quality_options if opt.quality == quality_option.quality
    ]

    # Step 2: Language selection
    language_option = select_language(same_quality_options)

    return language_option
