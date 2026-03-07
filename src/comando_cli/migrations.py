"""Database migration runner."""

from pathlib import Path

from yoyo import get_backend, read_migrations


def run_migrations(db_path: Path) -> None:
    """Run all pending migrations.

    Args:
        db_path: Path to SQLite database file
    """
    migrations_dir = Path(__file__).parent / "migrations"
    backend = get_backend(f"sqlite:///{db_path}")

    with backend.lock():
        all_migrations = read_migrations(str(migrations_dir))
        pending = backend.to_apply(all_migrations)
        backend.apply_migrations(pending)
