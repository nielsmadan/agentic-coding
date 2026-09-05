#!/usr/bin/env python3
"""Remove nono's `developer_instructions` from the live Codex config.

Codex injects `developer_instructions` into the model's prompt in its own
`<managed_developer_instructions>` tag — a channel separate from `AGENTS.md`. The
nono codex pack claims that slot (`wiring/codex-block.toml`) with advice telling the
agent to treat any `Operation not permitted` as a sandbox boundary and offer
`nono run --allow`. That produced repeated false denial reports.

This used to hold a competing copy of the text and write it back. It no longer does:
the same guidance reaches every harness through `loadout/instructions/sandbox.md`, so
there is nothing to replace nono's block *with* — it only has to go. `nono update`
puts it back, and this takes it out again on the next `./sync.sh`.

Deleting rather than replacing is the whole point: one document to maintain instead
of two, and no contest over who writes the key last.

Usage:
    python3 codex/strip_nono_block.py
    python3 codex/strip_nono_block.py --target /tmp/codex-config.toml
    python3 codex/strip_nono_block.py --check
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

DEFAULT_TARGET = Path.home() / ".codex" / "config.toml"
# Matches the assignment through its closing delimiter. Anchored to the start of a
# line so a `"""` inside another value cannot end the match early.
DEVELOPER_INSTRUCTIONS = re.compile(
    r'^developer_instructions\s*=\s*""".*?"""\n*', re.MULTILINE | re.DOTALL
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument(
        "--check", action="store_true", help="exit 1 if the key is present, changing nothing"
    )
    return parser.parse_args()


def strip(content: str) -> str:
    return DEVELOPER_INSTRUCTIONS.sub("", content)


def main() -> int:
    args = parse_args()
    if not args.target.is_file():
        print(f"note: {args.target} does not exist — nothing to strip")
        return 0
    content = args.target.read_text(encoding="utf-8")
    stripped = strip(content)
    if stripped == content:
        return 0
    if args.check:
        print(f"{args.target} still carries nono's developer_instructions", file=sys.stderr)
        return 1
    # Written through a temp file in the same directory so a crash cannot leave the
    # live config truncated.
    handle, temporary = tempfile.mkstemp(dir=args.target.parent, prefix=".codex-config-")
    with os.fdopen(handle, "w", encoding="utf-8") as out:
        out.write(stripped)
    os.replace(temporary, args.target)
    print(f"✓  Removed nono's developer_instructions from {args.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
