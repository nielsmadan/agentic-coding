#!/usr/bin/env python3
"""Merge repo-managed Codex config tables into the live user config.

Usage:
    python3 codex/sync_config.py
    python3 codex/sync_config.py --target /tmp/codex-config.toml
    python3 codex/sync_config.py --check
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "codex" / "config.toml"
DEFAULT_TARGET = Path.home() / ".codex" / "config.toml"
MANAGED_COMMENT = "# Managed by codex/config.toml via sync.sh."
TABLE_HEADER = re.compile(r"^\s*\[([^\[\]]+)\]\s*(?:#.*)?$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge repo-managed Codex config tables into a user config."
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help="config.toml to update",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if the target does not contain the managed config",
    )
    return parser.parse_args()


def table_path(line: str) -> str | None:
    match = TABLE_HEADER.match(line)
    return match.group(1).strip() if match else None


def managed_roots(source: str) -> tuple[str, ...]:
    roots = tuple(path for line in source.splitlines() if (path := table_path(line)))
    if not roots:
        raise ValueError(f"{SOURCE} must contain at least one TOML table")
    return roots


def is_owned(path: str, roots: tuple[str, ...]) -> bool:
    return any(path == root or path.startswith(f"{root}.") for root in roots)


def strip_owned_tables(content: str, roots: tuple[str, ...]) -> str:
    kept: list[str] = []
    skipping = False

    for line in content.splitlines():
        path = table_path(line)
        if path is not None:
            skipping = is_owned(path, roots)
        if not skipping and line != MANAGED_COMMENT:
            kept.append(line)

    while kept and not kept[-1].strip():
        kept.pop()
    return "\n".join(kept)


def render(current: str, source: str) -> str:
    tomllib.loads(source)
    roots = managed_roots(source)
    unmanaged = strip_owned_tables(current, roots)
    managed = source.strip()
    blocks = [block for block in (unmanaged, MANAGED_COMMENT, managed) if block]
    result = "\n\n".join(blocks) + "\n"
    tomllib.loads(result)
    return result


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".config-")
    try:
        with os.fdopen(fd, "w") as file:
            file.write(content)
        os.replace(temporary, path)
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


def main() -> int:
    args = parse_args()
    try:
        source = SOURCE.read_text()
        current = args.target.read_text() if args.target.exists() else ""
        expected = render(current, source)
    except (OSError, tomllib.TOMLDecodeError, ValueError) as error:
        print(f"codex config sync failed: {error}", file=sys.stderr)
        return 2

    if current == expected:
        print(f"codex config is up to date: {args.target}")
        return 0
    if args.check:
        print(f"codex config is out of date: {args.target}", file=sys.stderr)
        return 1

    try:
        atomic_write(args.target, expected)
    except OSError as error:
        print(f"codex config sync failed: {error}", file=sys.stderr)
        return 2
    print(f"wrote Codex config: {args.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
