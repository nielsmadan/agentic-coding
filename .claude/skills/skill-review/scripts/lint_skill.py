#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Mechanical quality checks for agent skills in this repo."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[4]
SKILL_ROOTS = (
    ("global", REPO / "loadout/skills"),
    ("kit", REPO / "loadout/kits/skills"),
    ("repo-local", REPO / ".claude/skills"),
)
HARNESS_KEYS = ("claude", "codex", "opencode", "pi")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s#]+)(?:#[^)]*)?\)")
WINDOWS_PATH_RE = re.compile(r"\b[\w-]+\\[\w-]+\\?[\w-]*\.(?:py|md|sh|js|ts|json)\b")
DATED_RE = re.compile(
    r"\b(?:before|after|until)\s+(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+)?20\d\d\b",
    re.IGNORECASE,
)
POV_RE = re.compile(r"^\s*(I\b|I'm\b|You\b|You can\b|We\b|Let me\b)")
TRIGGER_RE = re.compile(r"\buse\b[^.]{0,30}?\b(when|for|whenever|before|after|if)\b|\btriggers?\b|\binvoke",
                        re.IGNORECASE)
XML_TAG_RE = re.compile(r"<[A-Za-z/!?]")
ANCILLARY_RE = re.compile(r"^(LICENSE|THIRD_PARTY|NOTICE)|(^|/)\.|^agents/openai\.yaml$")

DESCRIPTION_MAX = 1024
LISTING_MAX = 1536
NAME_MAX = 64
BODY_LINES_MAX = 500
BODY_WORDS_MAX = 5000
REFERENCE_TOC_LINES = 100


@dataclass(frozen=True)
class Finding:
    skill: str
    severity: str
    check: str
    message: str
    line: int | None = None


@dataclass(frozen=True)
class Skill:
    name: str
    scope: str
    path: Path
    text: str
    files: tuple[str, ...]
    executable: frozenset[str]


def split_frontmatter(text: str) -> tuple[str | None, str, int]:
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, text, 1
    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if end is None:
        return None, text, 1
    return "\n".join(lines[1:end]), "\n".join(lines[end + 1:]), end + 2


def unfenced_lines(body: str, first_line: int) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    fenced = False
    for offset, line in enumerate(body.split("\n")):
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            result.append((first_line + offset, line))
    return result


def description_variants(meta: dict) -> list[tuple[str, dict]]:
    overrides = [(key, {**meta, **meta[key]}) for key in HARNESS_KEYS if isinstance(meta.get(key), dict)]
    return [("shared", meta), *overrides]


def check_frontmatter(skill: Skill) -> tuple[list[Finding], dict | None]:
    raw, _, _ = split_frontmatter(skill.text)
    if raw is None:
        return [Finding(skill.name, "error", "frontmatter", "SKILL.md has no `---` frontmatter block", 1)], None
    try:
        meta = yaml.safe_load(raw) or {}
    except yaml.YAMLError as err:
        reason = str(err).splitlines()[0]
        return [Finding(skill.name, "error", "frontmatter",
                        f"frontmatter is not valid YAML ({reason}); a strict parser drops its metadata, "
                        "usually an unquoted ': ' in a value")], None
    if not isinstance(meta, dict):
        return [Finding(skill.name, "error", "frontmatter", "frontmatter is not a mapping")], None
    tagged = [
        f"{key}{'' if variant == 'shared' else f' ({variant} override)'}"
        for variant, values in description_variants(meta)
        for key in ("name", "description")
        if XML_TAG_RE.search(str(values.get(key) or ""))
    ]
    return [Finding(skill.name, "error", "frontmatter",
                    f"`{key}` contains an XML-like tag; the spec forbids it and Claude Code escapes it")
            for key in tagged], meta


def check_name(skill: Skill, meta: dict) -> list[Finding]:
    name = meta.get("name")
    if not isinstance(name, str) or not name:
        return [Finding(skill.name, "error", "name", "missing `name`")]
    problems = [
        (not NAME_RE.match(name), "error", "`name` must be lowercase letters, digits and single hyphens"),
        (len(name) > NAME_MAX, "error", f"`name` is {len(name)} chars; the limit is {NAME_MAX}"),
        (name != skill.path.name, "error", f"`name` {name!r} does not match its directory {skill.path.name!r}"),
        (bool(re.search(r"claude|anthropic", name)), "warn", "`name` contains a reserved word (claude/anthropic)"),
    ]
    return [Finding(skill.name, severity, "name", message) for failed, severity, message in problems if failed]


def check_description(skill: Skill, meta: dict) -> list[Finding]:
    findings: list[Finding] = []
    for variant, values in description_variants(meta):
        label = "" if variant == "shared" else f" ({variant} override)"
        description = values.get("description")
        if not isinstance(description, str) or not description.strip():
            findings.append(Finding(skill.name, "error", "description", f"missing `description`{label}"))
            continue
        listing = len(description) + len(str(values.get("when_to_use") or ""))
        problems = [
            (len(description) > DESCRIPTION_MAX, "error",
             f"`description`{label} is {len(description)} chars; the spec limit is {DESCRIPTION_MAX}"),
            (listing > LISTING_MAX, "warn",
             f"description + when_to_use{label} is {listing} chars; Claude Code truncates the listing at {LISTING_MAX}"),
            (bool(POV_RE.match(description)), "warn",
             f"`description`{label} is not third person; it is injected into the system prompt"),
            (not TRIGGER_RE.search(description), "warn",
             f"`description`{label} names no trigger (no 'Use when/for …' or trigger phrases)"),
        ]
        findings.extend(Finding(skill.name, sev, "description", msg) for failed, sev, msg in problems if failed)
    return findings


def check_body(skill: Skill, known_skills: frozenset[str]) -> list[Finding]:
    _, body, first_line = split_frontmatter(skill.text)
    lines = body.strip("\n").split("\n")
    words = len(body.split())
    visible = unfenced_lines(body, first_line)
    headings = {line.strip().lstrip("#").strip().lower() for _, line in visible if line.startswith("## ")}
    prefixed = sorted({
        number
        for number, line in visible
        for match in re.finditer(r"(?<![\w/.~-])[/$]([a-z][a-z0-9-]+)\b", line)
        if match.group(1) in known_skills
    })
    findings = [
        *([Finding(skill.name, "warn", "size", f"body is {len(lines)} lines; keep SKILL.md under {BODY_LINES_MAX}")]
          if len(lines) > BODY_LINES_MAX else []),
        *([Finding(skill.name, "warn", "size", f"body is {words} words; this repo's ceiling is {BODY_WORDS_MAX}")]
          if words > BODY_WORDS_MAX else []),
        *[Finding(skill.name, "info", "sections", f"no `## {section.title()}` section")
          for section in ("examples", "troubleshooting") if section not in headings],
        *([Finding(skill.name, "info", "harness-prefix",
                   "`/name` or `$name` invocation syntax is harness-specific; write the bare skill name "
                   f"(lines {', '.join(map(str, prefixed))})", prefixed[0])] if prefixed else []),
        *[Finding(skill.name, "warn", "windows-path", f"backslash path {match.group(0)!r}", number)
          for number, line in visible for match in WINDOWS_PATH_RE.finditer(line)],
        *[Finding(skill.name, "info", "time-sensitive",
                  f"{match.group(0)!r} will go stale; move it to an 'old patterns' note or drop it", number)
          for number, line in visible for match in DATED_RE.finditer(line)],
    ]
    return findings


def link_targets(text: str) -> set[str]:
    _, body, first_line = split_frontmatter(text)
    visible = "\n".join(line for _, line in unfenced_lines(body, first_line))
    return {match.group(1).removeprefix("./") for match in LINK_RE.finditer(visible)
            if not re.match(r"^[a-z]+:", match.group(1))}


def mentions(text: str, path: str) -> bool:
    parent = path.rsplit("/", 1)[0] + "/" if "/" in path else None
    return path in text or Path(path).name in text or (parent is not None and parent in text)


def reachable(skill: Skill, supporting: list[str]) -> set[str]:
    texts = {"SKILL.md": skill.text}
    reached: set[str] = set()
    frontier = ["SKILL.md"]
    while frontier:
        text = texts[frontier.pop()]
        found = {f for f in supporting if f not in reached and mentions(text, f)}
        reached |= found
        for f in found:
            if f.endswith(".md"):
                texts[f] = (skill.path / f).read_text(errors="replace")
                frontier.append(f)
    return reached


def check_files(skill: Skill) -> list[Finding]:
    links = link_targets(skill.text)
    supporting = [f for f in skill.files if f != "SKILL.md"]
    broken = sorted(ref for ref in links if not ref.startswith("/") and not (skill.path / ref).exists())
    reached = reachable(skill, supporting)
    orphans = sorted(f for f in supporting
                     if f not in reached and not f.startswith("scripts/test_") and not ANCILLARY_RE.search(f))
    direct = {f for f in supporting if f in skill.text or Path(f).name in skill.text}
    nested = [
        (f, sorted(target for target in (
            str((skill.path / Path(f).parent / t).resolve().relative_to(skill.path.resolve(), walk_up=True))
            for t in link_targets((skill.path / f).read_text(errors="replace")))
            if target in supporting and target != f and target not in direct))
        for f in supporting if f.endswith(".md")
    ]
    long_without_toc = [
        f for f in supporting
        if f.endswith(".md")
        and (skill.path / f).read_text(errors="replace").count("\n") > REFERENCE_TOC_LINES
        and not re.search(r"^#+\s*(contents|table of contents)\b",
                          (skill.path / f).read_text(errors="replace"), re.IGNORECASE | re.MULTILINE)
    ]
    shebang_not_exec = [
        f for f in supporting
        if f.startswith("scripts/") and not f.startswith("scripts/test_")
        and (skill.path / f).read_text(errors="replace").startswith("#!") and f not in skill.executable
    ]
    return [
        *[Finding(skill.name, "warn", "links",
                  f"links `{ref}`, which does not exist here (fine if it is a template for the target project)")
          for ref in broken],
        *[Finding(skill.name, "warn", "orphan", f"`{f}` is never mentioned from SKILL.md or its references")
          for f in orphans],
        *[Finding(skill.name, "warn", "nesting",
                  f"`{f}` is the only way to reach {', '.join(targets)}; link it from SKILL.md to keep references one level deep")
          for f, targets in nested if targets],
        *[Finding(skill.name, "info", "toc", f"`{f}` is over {REFERENCE_TOC_LINES} lines with no contents list")
          for f in long_without_toc],
        *[Finding(skill.name, "warn", "script-mode", f"`{f}` has a shebang but is not executable")
          for f in shebang_not_exec],
    ]


def check_wiring(skill: Skill, classified: frozenset[str], readme: str, codex_links: frozenset[str]) -> list[Finding]:
    if skill.scope == "global":
        return [
            *([Finding(skill.name, "error", "publish", "not classified in publish/skills.toml")]
              if skill.name not in classified else []),
            *([Finding(skill.name, "info", "readme", "no row in loadout/skills/README.md")]
              if f"`/{skill.name}`" not in readme else []),
        ]
    if skill.scope == "repo-local" and skill.name not in codex_links:
        return [Finding(skill.name, "warn", "codex-link", f"no .codex/skills/{skill.name} symlink, so Codex never sees it")]
    return []


def lint(skill: Skill, known_skills: frozenset[str], classified: frozenset[str],
         readme: str, codex_links: frozenset[str]) -> list[Finding]:
    frontmatter, meta = check_frontmatter(skill)
    meta_findings = [*check_name(skill, meta), *check_description(skill, meta)] if meta is not None else []
    return [*frontmatter, *meta_findings, *check_body(skill, known_skills), *check_files(skill),
            *check_wiring(skill, classified, readme, codex_links)]


def load_skill(scope: str, path: Path) -> Skill:
    files = tuple(sorted(
        str(p.relative_to(path)) for p in path.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.name != ".DS_Store"
    ))
    executable = frozenset(f for f in files if os.access(path / f, os.X_OK))
    return Skill(path.name, scope, path, (path / "SKILL.md").read_text(errors="replace"), files, executable)


def discover() -> list[Skill]:
    return [
        load_skill(scope, entry)
        for scope, root in SKILL_ROOTS if root.is_dir()
        for entry in sorted(root.iterdir()) if (entry / "SKILL.md").is_file()
    ]


def publish_classified() -> frozenset[str]:
    manifest = REPO / "publish/skills.toml"
    if not manifest.is_file():
        return frozenset()
    import tomllib
    data = tomllib.loads(manifest.read_text())
    groups = [name for names in data.get("groups", {}).values() for name in names]
    return frozenset([*groups, *data.get("private", []), *data.get("local", [])])


def listing(skills: list[Skill]) -> str:
    def describe(skill: Skill) -> str:
        raw, _, _ = split_frontmatter(skill.text)
        try:
            meta = yaml.safe_load(raw or "") or {}
        except yaml.YAMLError:
            meta = {}
        return f"- {skill.name}: {meta.get('description', '(no description)')}"
    return "\n".join(describe(skill) for skill in skills)


def render_text(findings: list[Finding], checked: int) -> str:
    order = {"error": 0, "warn": 1, "info": 2}
    rows = [
        f"{f.severity:5}  {f.skill}  [{f.check}]{f' L{f.line}' if f.line else ''}  {f.message}"
        for f in sorted(findings, key=lambda f: (order[f.severity], f.skill, f.line or 0))
    ]
    counts = {sev: sum(f.severity == sev for f in findings) for sev in order}
    summary = f"{checked} skill(s) checked: {counts['error']} error, {counts['warn']} warn, {counts['info']} info"
    return "\n".join([*rows, summary])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("names", nargs="*", help="skill names; omit with --all")
    parser.add_argument("--all", action="store_true", help="check every skill in the repo")
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    parser.add_argument("--listing", action="store_true",
                        help="print every skill's name and description, for trigger tests")
    args = parser.parse_args(argv)

    skills = discover()
    if args.listing:
        print(listing(skills))
        return 0
    by_name = {skill.name: skill for skill in skills}
    unknown = [name for name in args.names if name not in by_name]
    if unknown or not (args.all or args.names):
        parser.error(f"unknown skill(s): {', '.join(unknown)}" if unknown else "name a skill or pass --all")
    selected = skills if args.all else [by_name[name] for name in args.names]

    readme_path = REPO / "loadout/skills/README.md"
    readme = readme_path.read_text() if readme_path.is_file() else ""
    codex_dir = REPO / ".codex/skills"
    codex_links = frozenset(p.name for p in codex_dir.iterdir()) if codex_dir.is_dir() else frozenset()
    known = frozenset(by_name)
    classified = publish_classified()
    findings = [f for skill in selected for f in lint(skill, known, classified, readme, codex_links)]

    print(json.dumps([asdict(f) for f in findings], indent=2) if args.json else render_text(findings, len(selected)))
    return 1 if any(f.severity == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
