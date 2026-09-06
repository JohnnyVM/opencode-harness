"""Install this repository's opencode files without replacing user files."""

import argparse
import os
from pathlib import Path
import sys


def source_root():
    """Return the repository root containing this script."""
    return Path(__file__).resolve().parent.parent


def _entries(source):
    entries = [(source / "opencode.jsonc", Path("opencode.jsonc"))]
    categories = (("agents", "*.md", False), ("skills", None, True), ("commands", "*.md", False))
    for category, pattern, directories_only in categories:
        directory = source / category
        if not directory.is_dir():
            continue
        candidates = directory.iterdir() if pattern is None else directory.glob(pattern)
        for candidate in sorted(candidates, key=lambda path: path.name):
            if (candidate.is_dir() if directories_only else candidate.is_file()):
                entries.append((candidate, Path(category) / candidate.name))
    return [entry for entry in entries if entry[0].is_file() or entry[0].is_dir()]


def install(source, home, dry_run=False):
    source = Path(source).resolve()
    destination_root = Path(home).expanduser() / ".config" / "opencode"
    try:
        entries = _entries(source)
    except OSError as error:
        print(f"error: cannot enumerate {source}: {error}", file=sys.stderr)
        return 1
    if not entries:
        print(f"error: source directory has no installable entries: {source}", file=sys.stderr)
        return 1

    failed = False
    for source_path, relative_destination in entries:
        destination = destination_root / relative_destination
        if os.path.lexists(destination):
            print(f"warning: skip existing destination {destination}")
            continue
        parent = destination.parent
        try:
            if not parent.exists():
                print(f"mkdir {parent}")
                if not dry_run:
                    parent.mkdir(parents=True, exist_ok=True)
            print(f"link {destination} -> {source_path.resolve()}")
            if not dry_run:
                os.symlink(str(source_path.resolve()), destination)
        except OSError as error:
            print(f"error: cannot install {destination}: {error}", file=sys.stderr)
            failed = True
    return 1 if failed else 0


def main(argv=None, *, home=None, repository=None):
    parser = argparse.ArgumentParser(description="Install opencode configuration links")
    parser.add_argument("--dry-run", action="store_true", help="report changes without making them")
    args = parser.parse_args(argv)
    root = source_root() if repository is None else Path(repository).resolve()
    target_home = Path.home() if home is None else home
    return install(root / "opencode", target_home, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
