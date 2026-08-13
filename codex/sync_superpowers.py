#!/usr/bin/env python3
"""Make installed Codex Superpowers skills explicit-invocation only."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path


DEFAULT_CACHE = Path.home() / ".codex" / "plugins" / "cache"
POLICY_HEADER = re.compile(r"^policy:\s*$")
POLICY_KEY = re.compile(r"^(\s+)allow_implicit_invocation\s*:.*$")
TOP_LEVEL_KEY = re.compile(r"^[^\s#][^:]*:")


def explicit_only_metadata(content: str) -> str:
    lines = content.splitlines()
    policy_index = next(
        (index for index, line in enumerate(lines) if POLICY_HEADER.match(line)),
        None,
    )

    if policy_index is None:
        if any(line.startswith("policy:") for line in lines):
            raise ValueError("unsupported inline policy metadata")
        prefix = content.rstrip()
        separator = "\n\n" if prefix else ""
        return f"{prefix}{separator}policy:\n  allow_implicit_invocation: false\n"

    policy_end = len(lines)
    for index in range(policy_index + 1, len(lines)):
        if TOP_LEVEL_KEY.match(lines[index]):
            policy_end = index
            break

    for index in range(policy_index + 1, policy_end):
        match = POLICY_KEY.match(lines[index])
        if match:
            lines[index] = f"{match.group(1)}allow_implicit_invocation: false"
            return "\n".join(lines) + "\n"

    lines.insert(policy_index + 1, "  allow_implicit_invocation: false")
    return "\n".join(lines) + "\n"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".openai-")
    try:
        with os.fdopen(descriptor, "w") as file:
            file.write(content)
        os.replace(temporary, path)
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


def superpowers_plugins(cache: Path) -> list[Path]:
    plugins: list[Path] = []
    for manifest in cache.glob("*/superpowers/*/.codex-plugin/plugin.json"):
        try:
            metadata = json.loads(manifest.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if metadata.get("name") == "superpowers":
            plugins.append(manifest.parent.parent)
    return sorted(plugins)


def reconcile(cache: Path) -> tuple[int, int, int]:
    plugins = superpowers_plugins(cache)
    skill_count = 0
    changed_count = 0

    for plugin in plugins:
        for skill_file in sorted((plugin / "skills").glob("*/SKILL.md")):
            skill_count += 1
            metadata = skill_file.parent / "agents" / "openai.yaml"
            current = metadata.read_text() if metadata.exists() else ""
            expected = explicit_only_metadata(current)
            if current != expected:
                atomic_write(metadata, expected)
                changed_count += 1

    return len(plugins), skill_count, changed_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Disable implicit invocation for installed Superpowers skills."
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=DEFAULT_CACHE,
        help="Codex plugin cache root",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plugins, skills, changed = reconcile(args.cache)
    if not plugins:
        print("Codex Superpowers plugin is not installed; skipping")
        return 0
    print(
        f"configured {skills} Superpowers skills for explicit invocation "
        f"({changed} changed)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
