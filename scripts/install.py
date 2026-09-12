"""Install this repository's opencode files without replacing user files."""

import argparse
import os
from pathlib import Path
import sys


def source_root():
    """Return the repository root containing this script."""
    return Path(__file__).resolve().parent.parent


def _entries(source):
    entries = []

    config = source / "opencode.jsonc"
    if config.is_file():
        entries.append((config, Path(config.name)))

    for path in sorted((source / "agents").glob("*.md")):
        if path.is_file():
            entries.append((path, Path("agents") / path.name))

    skills = source / "skills"
    if skills.is_dir():
        for path in sorted(skills.iterdir()):
            if path.is_dir() and (path / "SKILL.md").is_file():
                entries.append((path, Path("skills") / path.name))

    for path in sorted((source / "commands").glob("*.md")):
        if path.is_file():
            entries.append((path, Path("commands") / path.name))

    return entries


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
        target = source_path.resolve()
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
            print(f"link {destination} -> {target}")
            if not dry_run:
                os.symlink(str(target), destination)
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
