#!/usr/bin/env python3
"""Own `developer_instructions` in the live Codex config.

Everything else this script used to merge — `[mcp_servers.*]`, `[plugins.*]`,
`[marketplaces.*]` and the model defaults — is loadout's now: it writes
~/.codex/config.toml directly, stripping the keys it declares and leaving the
rest alone. What remains here is the one key loadout cannot hold, because
`developer_instructions` is a multi-line TOML string and loadout's surgery works
line-wise over top-level scalars.

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
DEFAULT_TARGET = Path.home() / ".codex" / "config.toml"
INSTRUCTIONS_SOURCE = REPO_ROOT / "codex" / "developer-instructions.md"
TABLE_HEADER = re.compile(r"^\s*\[([^\[\]]+)\]\s*(?:#.*)?$")
DEVELOPER_INSTRUCTIONS = re.compile(
    r'^developer_instructions\s*=\s*""".*?"""\n*', re.MULTILINE | re.DOTALL
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Own developer_instructions in a Codex user config."
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
        help="exit 1 if the target does not carry the managed instructions",
    )
    return parser.parse_args()


def table_path(line: str) -> str | None:
    match = TABLE_HEADER.match(line)
    return match.group(1).strip() if match else None


def set_developer_instructions(content: str) -> str:
    """Own the top-level `developer_instructions` key.

    The nono codex pack injects its own copy, which tells the agent to treat any
    `Operation not permitted` as a sandbox boundary and offer `nono run --allow`.
    That produced repeated false denial reports, so ours replaces it — and a
    `nono update` puts the pack's back, which this undoes on the next sync.

    The key must sit above the first table header or TOML reads it as a member of
    the preceding table.
    """
    if not INSTRUCTIONS_SOURCE.exists():
        return content

    body = INSTRUCTIONS_SOURCE.read_text().strip()
    block = f'developer_instructions = """\n{body}\n"""'

    content = DEVELOPER_INSTRUCTIONS.sub("", content)
    lines = content.splitlines()
    for index, line in enumerate(lines):
        if table_path(line) is not None:
            # Blank line after the block: loadout writes one between the preamble
            # and the first table, and without it the two writers disagree by a
            # newline forever — `loadout check` reports drift on every run.
            return "\n".join(lines[:index] + [block, ""] + lines[index:]) + "\n"
    return content.rstrip() + "\n\n" + block


def render(current: str) -> str:
    result = set_developer_instructions(current)
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
        current = args.target.read_text() if args.target.exists() else ""
        expected = render(current)
    except (OSError, tomllib.TOMLDecodeError, ValueError) as error:
        print(f"codex config sync failed: {error}", file=sys.stderr)
        return 2

    if current == expected:
        print(f"codex developer instructions are up to date: {args.target}")
        return 0
    if args.check:
        print(f"codex developer instructions are out of date: {args.target}", file=sys.stderr)
        return 1

    try:
        atomic_write(args.target, expected)
    except OSError as error:
        print(f"codex config sync failed: {error}", file=sys.stderr)
        return 2
    print(f"wrote Codex developer instructions: {args.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
