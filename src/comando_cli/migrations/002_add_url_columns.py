"""Add title_url and magnet_url columns."""

from yoyo import step

steps = [
    step(
        "ALTER TABLE watch_history ADD COLUMN title_url TEXT",
        "ALTER TABLE watch_history DROP COLUMN title_url",
    ),
    step(
        "ALTER TABLE watch_history ADD COLUMN magnet_url TEXT",
        "ALTER TABLE watch_history DROP COLUMN magnet_url",
    ),
]
