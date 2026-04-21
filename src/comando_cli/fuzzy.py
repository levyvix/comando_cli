"""Fuzzy selection helpers backed by pyfzf."""

from typing import Sequence


def select_with_fzf(labels: Sequence[str], *, prompt: str, height: str) -> str | None:
    """Return the selected label using pyfzf, or None when unavailable/cancelled."""
    try:
        from pyfzf.pyfzf import FzfPrompt
    except ImportError:
        return None

    try:
        selector = FzfPrompt()
        escaped_prompt = prompt.replace('"', '\\"')
        selected = selector.prompt(
            list(labels),
            fzf_options=f'--prompt="{escaped_prompt}" --height={height} --reverse',
        )
    except (FileNotFoundError, OSError):
        return None

    if not selected:
        return None

    value = selected[0].strip()
    return value or None
