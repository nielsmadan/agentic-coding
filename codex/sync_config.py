#!/usr/bin/env python3
"""Merge repo-managed Codex config tables into the live user config.

Usage:
    python3 codex/sync_config.py
    python3 codex/sync_config.py --target /tmp/codex-config.toml
    python3 codex/sync_config.py --check
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "codex" / "config.toml"
PERMISSIONS_SOURCE = REPO_ROOT / "codex" / "mcp-permissions.toml"
DEFAULT_TARGET = Path.home() / ".codex" / "config.toml"
MANAGED_COMMENT = "# Managed by codex/config.toml via sync.sh."
INSTRUCTIONS_SOURCE = REPO_ROOT / "codex" / "developer-instructions.md"
MODEL_DEFAULTS_SOURCE = REPO_ROOT / "codex" / "model-defaults.toml"
TABLE_HEADER = re.compile(r"^\s*\[([^\[\]]+)\]\s*(?:#.*)?$")


def merge_dict(base: dict, overlay: dict) -> dict:
    result = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def toml_key(value: str) -> str:
    return value if re.fullmatch(r"[A-Za-z0-9_-]+", value) else json.dumps(value)


def toml_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    if isinstance(value, (int, float)):
        return str(value)
    raise ValueError(f"unsupported managed TOML value: {value!r}")


def render_toml(data: dict) -> str:
    lines: list[str] = []

    def emit(table: dict, path: tuple[str, ...]) -> None:
        scalars = {key: value for key, value in table.items() if not isinstance(value, dict)}
        children = {key: value for key, value in table.items() if isinstance(value, dict)}
        if path and scalars:
            if lines:
                lines.append("")
            lines.append("[" + ".".join(toml_key(part) for part in path) + "]")
            for key, value in scalars.items():
                lines.append(f"{toml_key(key)} = {toml_value(value)}")
        elif not path and scalars:
            for key, value in scalars.items():
                lines.append(f"{toml_key(key)} = {toml_value(value)}")
        for key, value in children.items():
            emit(value, path + (key,))

    emit(data, ())
    return "\n".join(lines) + "\n"


def load_managed_source() -> str:
    base = tomllib.loads(SOURCE.read_text())
    overlay = (
        tomllib.loads(PERMISSIONS_SOURCE.read_text())
        if PERMISSIONS_SOURCE.exists()
        else {}
    )
    return render_toml(merge_dict(base, overlay))


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


ASSIGNMENT = re.compile(r"^\s*([A-Za-z0-9_-]+)\s*=")


def set_model_defaults(content: str) -> str:
    """Own the top-level keys named in codex/model-defaults.toml.

    Codex rewrites this file as it goes — project trust entries, plugins — so the
    keys are replaced where they already sit rather than the file being rebuilt.
    Like developer_instructions they must stay above the first table header, or
    TOML reads them as members of the preceding table.
    """
    if not MODEL_DEFAULTS_SOURCE.exists():
        return content

    defaults = tomllib.loads(MODEL_DEFAULTS_SOURCE.read_text())
    if any(isinstance(value, dict) for value in defaults.values()):
        raise ValueError(f"{MODEL_DEFAULTS_SOURCE} may only hold top-level keys")
    if not defaults:
        return content

    lines = content.splitlines()
    first_table = next(
        (index for index, line in enumerate(lines) if table_path(line) is not None),
        len(lines),
    )

    pending = dict(defaults)
    kept: list[str] = []
    for index, line in enumerate(lines):
        match = ASSIGNMENT.match(line) if index < first_table else None
        if match and match.group(1) in pending:
            key = match.group(1)
            kept.append(f"{toml_key(key)} = {toml_value(pending.pop(key))}")
        else:
            kept.append(line)

    if pending:
        block = [f"{toml_key(key)} = {toml_value(value)}" for key, value in pending.items()]
        # Land beside the other top-level scalars, not against the first table
        # header — that sits below nono's marker, where these would read as part
        # of its managed block.
        last = max(
            (index for index in range(first_table) if ASSIGNMENT.match(lines[index])),
            default=None,
        )
        at = first_table if last is None else last + 1
        kept = kept[:at] + block + kept[at:]
    return "\n".join(kept) + "\n"


DEVELOPER_INSTRUCTIONS = re.compile(
    r'^developer_instructions\s*=\s*""".*?"""\n*', re.MULTILINE | re.DOTALL
)


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
            return "\n".join(lines[:index] + [block] + lines[index:]) + "\n"
    return content.rstrip() + "\n\n" + block


def render(current: str, source: str) -> str:
    tomllib.loads(source)
    roots = managed_roots(source)
    unmanaged = strip_owned_tables(current, roots)
    # The model keys belong to the preserved region, so they are set before the
    # blocks are composed — otherwise a target that started empty gains them
    # above the managed comment on one run and below it on the next.
    # developer_instructions is re-inserted afterwards; dropping it first keeps
    # its multiline body out of the region set_model_defaults edits by line.
    unmanaged = set_model_defaults(DEVELOPER_INSTRUCTIONS.sub("", unmanaged))
    managed = source.strip()
    blocks = [
        stripped
        for block in (unmanaged, MANAGED_COMMENT, managed)
        if (stripped := block.strip("\n"))
    ]
    result = set_developer_instructions("\n\n".join(blocks) + "\n")
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
        source = load_managed_source()
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
