"""Render the publishable skill subset into a standalone repository tree.

Run as a script path (`python3 publish/sync.py`), never `python3 -m publish.sync`:
from the repo root the latter puts the repo root on sys.path, where the `loadout/`
config directory shadows the installed `loadout` package as a namespace package
and imports successfully with `__file__` set to None.
"""

from __future__ import annotations

import json
import re
import shutil
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "publish" / "skills.toml"
SKILLS_ROOT = REPO_ROOT / "loadout" / "skills"


def load_manifest(path: Path) -> tuple[list[str], list[str]]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return list(data.get("publish", [])), list(data.get("private", []))


def available_skills(skills_root: Path) -> list[str]:
    return sorted(
        entry.name
        for entry in skills_root.iterdir()
        if entry.is_dir() and (entry / "SKILL.md").is_file()
    )


def manifest_errors(
    available: list[str], publish: list[str], private: list[str]
) -> list[str]:
    errors: list[str] = []
    for name in sorted(set(publish) & set(private)):
        errors.append(f"{name}: listed in both publish and private")
    classified = set(publish) | set(private)
    for name in available:
        if name not in classified:
            errors.append(
                f"{name}: unclassified — add it to publish or private "
                f"in publish/skills.toml"
            )
    for name in sorted(classified - set(available)):
        errors.append(f"{name}: listed in publish/skills.toml but no such skill")
    return errors


def check_manifest() -> list[str]:
    publish, private = load_manifest(MANIFEST_PATH)
    return manifest_errors(available_skills(SKILLS_ROOT), publish, private)


# `/Users/nielsmadan`, not `/Users/` — the risk is identity leaking, not the
# literal prefix. `doc/references/` legitimately uses `/Users/name/projects/app`
# as an example of a path NOT to write, and mode-review.md tells the reader to
# grep for `/Users/`. Broadening this re-breaks both.
PERSONAL = re.compile(r"~/(?:ac|rc|wrksp)\b|/Users/nielsmadan|nielsmadan@|quantumcraft")
MARKER = re.compile(r"^::: ?", re.M)
_KEY = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$")
_FENCE = re.compile(r"^---\s*$")
_BLOCK = re.compile(r"^[>|][+-]?$")

MAX_NAME = 64
MAX_DESCRIPTION = 1024


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    lines = text.split("\n")[1:]
    end = next((i for i, line in enumerate(lines) if _FENCE.match(line)), None)
    if end is None:
        return {}
    values: dict[str, str] = {}
    i = 0
    while i < end:
        match = _KEY.match(lines[i])
        i += 1
        if not match:
            continue
        key, raw = match.group(1), match.group(2).strip()
        if _BLOCK.match(raw):
            # both block styles fold to spaces: values feed the length guard
            # and one-line README table cells
            parts: list[str] = []
            while i < end and (not lines[i].strip() or lines[i][0] in " \t"):
                if lines[i].strip():
                    parts.append(lines[i].strip())
                i += 1
            values[key] = " ".join(parts)
        else:
            parts = [raw] if raw else []
            while i < end and lines[i].strip() and lines[i][0] in " \t":
                parts.append(lines[i].strip())
                i += 1
            values[key] = _unquote(" ".join(parts))
    return values


def reference_pattern(name: str) -> re.Pattern[str]:
    escaped = re.escape(name)
    # Zero-width leading context so match.start() lands on the reference itself,
    # keeping _line_of accurate for matches at the start of a line.
    return re.compile(rf"(?:(?<=[\s`])|^)/{escaped}\b|`{escaped}`", re.M)


def guard_errors(name: str, text: str, private: list[str]) -> list[str]:
    errors: list[str] = []
    for match in PERSONAL.finditer(text):
        line = _line_of(text, match.start())
        errors.append(
            f"{name}: personal string {match.group(0)!r} (SKILL.md:{line})"
        )
    frontmatter = parse_frontmatter(text)
    declared = frontmatter.get("name", "")
    if declared != name:
        errors.append(f"{name}: frontmatter name {declared!r} does not match directory")
    if len(declared) > MAX_NAME:
        errors.append(f"{name}: name is {len(declared)} chars, max {MAX_NAME}")
    description = frontmatter.get("description", "")
    if not description:
        errors.append(f"{name}: description is empty")
    elif len(description) > MAX_DESCRIPTION:
        errors.append(
            f"{name}: description is {len(description)} chars, max {MAX_DESCRIPTION}"
        )
    if "|" in description:
        errors.append(
            f"{name}: description contains '|', which breaks the README table"
        )
    for other in private:
        if reference_pattern(other).search(text):
            errors.append(f"{name}: references unpublished skill {other!r}")
    return errors


def marker_warnings(name: str, text: str) -> list[str]:
    if MARKER.search(text):
        return [f"{name}: still contains ::: harness markers after rendering"]
    return []


def tree_guard_errors(tree: Path, private: list[str]) -> list[str]:
    skills_dir = tree / "skills"
    if not skills_dir.is_dir():
        return [f"{skills_dir}: skills directory missing"]
    errors: list[str] = []
    for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        document = skill_dir / "SKILL.md"
        if not document.is_file():
            errors.append(f"{skill_dir.name}: missing SKILL.md")
            continue
        errors.extend(
            guard_errors(skill_dir.name, document.read_text(encoding="utf-8"), private)
        )
        for support in sorted(skill_dir.rglob("*")):
            if not support.is_file() or support == document:
                continue
            content = support.read_text(encoding="utf-8", errors="ignore")
            relative = support.relative_to(skills_dir)
            for match in PERSONAL.finditer(content):
                line = _line_of(content, match.start())
                errors.append(
                    f"{relative}:{line}: personal string {match.group(0)!r}"
                )
            for other in private:
                for match in reference_pattern(other).finditer(content):
                    line = _line_of(content, match.start())
                    errors.append(
                        f"{relative}:{line}: references unpublished skill {other!r}"
                    )
    return errors


LOADOUT_BANNER = re.compile(
    r"^<!-- Generated by loadout from skills/.*?-->$", re.M
)
PROVENANCE = (
    "<!-- Generated from https://github.com/nielsmadan/agentic-coding — "
    "edits here are overwritten. -->"
)
HARNESS = "claude"


@dataclass(frozen=True)
class FakeSkill:
    """Test double matching the shape render_tree needs from loadout's Skill."""

    name: str
    document: Path
    supporting: tuple[Path, ...]


def swap_banner(text: str) -> str:
    return LOADOUT_BANNER.sub(PROVENANCE, text, count=1)


def render_tree(
    out: Path,
    names: list[str],
    skills: Sequence[Any],
    render: Callable[[Any, str], str],
) -> None:
    """Rebuild <out>/skills/ only. Never touch the output root — .github/ lives there."""
    destination = out / "skills"
    if destination.exists():
        shutil.rmtree(destination)
    wanted = set(names)
    for skill in skills:
        if skill.name not in wanted:
            continue
        skill_out = destination / skill.name
        skill_out.mkdir(parents=True)
        document = swap_banner(render(skill, HARNESS))
        (skill_out / "SKILL.md").write_text(document, encoding="utf-8")
        source_dir = skill.document.parent
        for relative in skill.supporting:
            target = skill_out / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_dir / relative, target)


def load_loadout() -> tuple[Callable, Callable]:
    try:
        from loadout.skills import discover_skills, render_skill
    # ImportError, not ModuleNotFoundError: the shadowing case this message
    # describes imports the namespace package fine and fails on the symbols.
    except ImportError:
        raise SystemExit(
            "loadout is not importable. Install it with:\n"
            "  pip install 'git+https://github.com/nielsmadan/loadout'\n"
            "Note: run this file as a script path, not with -m, or the loadout/ "
            "config directory shadows the package."
        )
    return discover_skills, render_skill


MARKETPLACE_NAME = "nlsmdn"
PLUGIN_NAME = "nlsmdn"
OWNER = {"name": "Niels Madan", "url": "https://github.com/nielsmadan"}
HOMEPAGE = "https://github.com/nielsmadan/skills"
SUMMARY = "Opinionated agent skills for code review, research, and daily workflow"

LICENSE_TEXT = """MIT License

Copyright (c) 2026 Niels Madan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def build_marketplace() -> dict:
    return {
        "name": MARKETPLACE_NAME,
        "owner": dict(OWNER),
        "description": SUMMARY,
        "plugins": [
            {"name": PLUGIN_NAME, "source": "./", "description": SUMMARY}
        ],
    }


def build_plugin() -> dict:
    return {
        "name": PLUGIN_NAME,
        "description": SUMMARY,
        "author": dict(OWNER),
        "homepage": HOMEPAGE,
        "license": "MIT",
    }


def build_readme(entries: list[tuple[str, str]]) -> str:
    rows = "\n".join(f"| `{name}` | {description} |" for name, description in entries)
    return f"""# nlsmdn skills

{SUMMARY}. {len(entries)} skills, generated from
[nielsmadan/agentic-coding](https://github.com/nielsmadan/agentic-coding) — do not edit this repo
directly, changes are overwritten.

## Install

Claude Code, as a plugin:

```
claude plugin marketplace add nielsmadan/skills
claude plugin install nlsmdn@nlsmdn
```

Skills then appear as `/nlsmdn:code-review` and so on.

Any other agent (Codex, Cursor, OpenCode, Zed, Copilot CLI, Gemini CLI, Amp):

```
npx skills add nielsmadan/skills
```

Add `--skill <name>` to install one, or `--all` to cover every detected agent.

## Notes

- Third-party marketplaces default to **auto-update off**. Enable it per
  marketplace in `/plugin`, or run `claude plugin update nlsmdn` when you want
  changes.
- There is no `version` field: the version resolves to the source commit SHA, so
  every push is available immediately to anyone who updates.
- Codex caps its skill catalog at 2% of the context window (or 8,000 characters)
  and drops skills past that. Installing all {len(entries)} at once will exceed
  it — prefer `--skill` to pick the ones you want.
- Some skills declare a `compatibility` requirement (an external CLI). Those
  degrade gracefully when the tool is absent.

## Skills

| Skill | Description |
|---|---|
{rows}

## License

MIT
"""


def write_artifacts(out: Path, entries: list[tuple[str, str]]) -> None:
    plugin_dir = out / ".claude-plugin"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "marketplace.json").write_text(
        json.dumps(build_marketplace(), indent=2) + "\n", encoding="utf-8"
    )
    (plugin_dir / "plugin.json").write_text(
        json.dumps(build_plugin(), indent=2) + "\n", encoding="utf-8"
    )
    (out / "LICENSE").write_text(LICENSE_TEXT, encoding="utf-8")
    (out / "README.md").write_text(build_readme(entries), encoding="utf-8")


def build(out: Path) -> tuple[list[str], list[str]]:
    """Render everything into `out`. Returns (errors, warnings)."""
    publish, private = load_manifest(MANIFEST_PATH)
    errors = manifest_errors(available_skills(SKILLS_ROOT), publish, private)
    if errors:
        return errors, []
    discover_skills, render_skill = load_loadout()
    skills = discover_skills(SKILLS_ROOT)
    render_tree(out, publish, skills, render_skill)
    entries: list[tuple[str, str]] = []
    warnings: list[str] = []
    for name in sorted(publish):
        text = (out / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        entries.append((name, parse_frontmatter(text).get("description", "")))
        warnings.extend(marker_warnings(name, text))
    write_artifacts(out, entries)
    return tree_guard_errors(out, private), warnings


def main() -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-manifest",
        action="store_true",
        help="exit 1 if any skill is unclassified",
    )
    parser.add_argument(
        "--out", type=Path, help="render the published tree into this directory"
    )
    args = parser.parse_args()
    if args.check_manifest:
        errors = check_manifest()
        for error in errors:
            print(f"publish: {error}", file=sys.stderr)
        return 1 if errors else 0
    if args.out:
        errors, warnings = build(args.out)
        for warning in warnings:
            print(f"publish: warning: {warning}", file=sys.stderr)
        for error in errors:
            print(f"publish: {error}", file=sys.stderr)
        return 1 if errors else 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
