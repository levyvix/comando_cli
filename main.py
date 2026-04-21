from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from comando_cli.cli import app


def main():
    app()


if __name__ == "__main__":
    main()
