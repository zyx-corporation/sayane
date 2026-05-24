"""Sayane CLI entry point."""

from sayane.cli.app import build_app
from sayane.cli.i18n import init_locale_from_argv, set_locale

# Default app for tests and `from sayane.cli.main import app` (English).
set_locale("en")
app = build_app()


def main() -> None:
    """Run CLI with locale resolved from --lang / SAYANE_LANG / LANG."""
    init_locale_from_argv()
    build_app()()


if __name__ == "__main__":
    main()
