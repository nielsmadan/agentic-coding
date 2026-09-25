#!/usr/bin/env python3
"""Remove the nono codex pack's block from ~/.codex/config.toml, keeping everything else."""

from __future__ import annotations

import argparse
import os
import re
import tempfile
import tomllib
from pathlib import Path


DEFAULT_CONFIG = Path.home() / ".codex" / "config.toml"
MARKER = re.compile(r"^# (>>>|<<<) nono:nolabs-ai-codex (>>>|<<<)$")
INSTRUCTIONS_START = re.compile(r'^developer_instructions\s*=\s*"""')


def strip_nono_block(content: str) -> str:
    kept: list[str] = []
    in_block = False
    in_instructions = False
    for line in content.splitlines(keepends=True):
        if MARKER.match(line.rstrip("\n")):
            in_block = line.startswith("# >>>")
            continue
        if in_instructions:
            in_instructions = not line.rstrip().endswith('"""')
            continue
        if in_block and INSTRUCTIONS_START.match(line):
            in_instructions = line.rstrip().count('"""') < 2
            continue
        kept.append(line)
    return "".join(kept)


def atomic_write(path: Path, content: str) -> None:
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".config-")
    try:
        with os.fdopen(descriptor, "w") as file:
            file.write(content)
        os.replace(temporary, path)
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    return parser.parse_args()


def main() -> int:
    config = parse_args().config
    if not config.exists():
        return 0
    current = config.read_text()
    stripped = strip_nono_block(current)
    if stripped == current:
        return 0
    tomllib.loads(stripped)
    atomic_write(config, stripped)
    print(f"✓  Removed the nono codex pack block from {config}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
