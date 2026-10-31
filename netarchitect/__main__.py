"""Allow both ``python -m netarchitect`` and direct __main__.py execution."""

if __package__:
    from .cli import main
else:
    # When this file is run by path, Python puts the package directory (rather
    # than its parent) on sys.path and relative imports have no package context.
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))
    from netarchitect.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

