#!/usr/bin/env python3
"""Count skill invocations across Claude, Codex, Droid, OpenCode and Pi session logs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator

REPO = Path(__file__).resolve().parents[4]
_SEARCH_PATH = REPO / "loadout/skills/check-agent-logs/scripts/search_agent_logs.py"
_SPEC = importlib.util.spec_from_file_location("search_agent_logs", _SEARCH_PATH)
sal = importlib.util.module_from_spec(_SPEC)
# dataclasses resolves string annotations through sys.modules during exec.
sys.modules["search_agent_logs"] = sal
# A .pyc beside the loadout source trips the publish scan for personal strings.
_WROTE_BYTECODE, sys.dont_write_bytecode = sys.dont_write_bytecode, True
_SPEC.loader.exec_module(sal)
sys.dont_write_bytecode = _WROTE_BYTECODE

AGENTS = ("claude", "codex", "droid", "opencode", "pi")
USER, MODEL = "user", "model"

CLAUDE_BASE_DIR = re.compile(r"^Base directory for this skill:\s*(\S+)")
CODEX_SKILL_BLOCK = re.compile(r"<skill>\s*<name>([^<\s]+)</name>")
SKILL_ATTR_BLOCK = re.compile(r'<skill name="([^"]+)"')
AUTOMATION_CWD = re.compile(r"^/(?:private/)?(?:tmp|var/folders)/|/\.sandbox/")
INSTALLED_SKILL_FILE = re.compile(
    r"/\.(?:claude|codex|agents|factory|pi/agent|config/opencode)/(?:[^\s\"'`;|]*/)?"
    r"skills/([A-Za-z0-9_.:-]+)/SKILL\.md"
)


@dataclass(frozen=True)
class Event:
    agent: str
    session: str
    cwd: str | None
    timestamp: str | None
    skill: str
    trigger: str


def skill_name(raw: str) -> str:
    return raw.rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1]


def text_blocks(content: object) -> list[str]:
    if isinstance(content, str):
        return [content]
    if not isinstance(content, list):
        return []
    return [str(b.get("text", "")) for b in content
            if isinstance(b, dict) and b.get("type") in ("text", "input_text")]


def installed_reads(value: object) -> set[str]:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return {skill_name(m) for m in INSTALLED_SKILL_FILE.findall(text)}


def claude_skills(record: dict) -> list[tuple[str, str]]:
    if record.get("type") != "user" or not record.get("isMeta"):
        return []
    content = (record.get("message") or {}).get("content")
    trigger = MODEL if record.get("sourceToolUseID") else USER
    return [(skill_name(m.group(1)), trigger)
            for m in map(CLAUDE_BASE_DIR.match, text_blocks(content)) if m]


def codex_skills(record: dict) -> list[tuple[str, str]]:
    payload = record.get("payload")
    if record.get("type") != "response_item" or not isinstance(payload, dict):
        return []
    kind = payload.get("type")
    if kind == "message" and payload.get("role") == "user":
        return [(skill_name(n), USER)
                for t in text_blocks(payload.get("content")) for n in CODEX_SKILL_BLOCK.findall(t)]
    if kind in ("function_call", "custom_tool_call", "local_shell_call"):
        args = payload.get("arguments") or payload.get("input") or payload.get("action")
        return [(s, MODEL) for s in installed_reads(args)]
    return []


def droid_skills(record: dict) -> list[tuple[str, str]]:
    message = record.get("message")
    if record.get("type") != "message" or not isinstance(message, dict):
        return []
    content = message.get("content")
    if message.get("role") == "user":
        return [(skill_name(n), USER)
                for t in text_blocks(content) for n in SKILL_ATTR_BLOCK.findall(t)]
    if not isinstance(content, list):
        return []
    return [(skill_name(str(b["input"]["skill"])), MODEL) for b in content
            if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Skill"
            and isinstance(b.get("input"), dict) and b["input"].get("skill")]


def pi_skills(record: dict) -> list[tuple[str, str]]:
    message = record.get("message")
    if record.get("type") != "message" or not isinstance(message, dict):
        return []
    content = message.get("content")
    if message.get("role") == "user":
        return [(skill_name(n), USER)
                for t in text_blocks(content) for n in SKILL_ATTR_BLOCK.findall(t)]
    if not isinstance(content, list):
        return []
    return [(s, MODEL) for b in content
            if isinstance(b, dict) and b.get("type") == "toolCall"
            for s in installed_reads(b.get("arguments"))]


def opencode_skills(part: dict) -> list[tuple[str, str]]:
    if part.get("type") != "tool" or part.get("tool") != "skill":
        return []
    name = ((part.get("state") or {}).get("input") or {}).get("name")
    return [(skill_name(str(name)), MODEL)] if name else []


def dedupe_reads(events: list[Event]) -> list[Event]:
    """A model reading SKILL.md in several chunks is one load, so file-read events
    count once per session and skill; explicit invocations all count."""
    seen: set[tuple[str, str]] = set()
    kept = []
    for e in events:
        key = (e.session, e.skill)
        if e.trigger == MODEL and e.agent in ("codex", "pi"):
            if key in seen:
                continue
            seen.add(key)
        kept.append(e)
    return kept


@dataclass(frozen=True)
class SessionHeader:
    session: str
    cwd: str | None


JSONL_HEADERS: dict[str, Callable[[dict], SessionHeader | None]] = {
    "codex": lambda r: SessionHeader(str(r["payload"].get("id") or ""), r["payload"].get("cwd"))
    if r.get("type") == "session_meta" and isinstance(r.get("payload"), dict) else None,
    "droid": lambda r: SessionHeader(str(r.get("id") or ""), r.get("cwd"))
    if r.get("type") == "session_start" else None,
    "pi": lambda r: SessionHeader(str(r.get("id") or ""), r.get("cwd"))
    if r.get("type") == "session" else None,
}
DETECTORS = {"claude": claude_skills, "codex": codex_skills, "droid": droid_skills,
             "pi": pi_skills}


def jsonl_events(agent: str, path: Path, options) -> list[Event]:
    session, cwd = path.stem, None
    events: list[Event] = []
    for record in sal.jsonl_records(path):
        header = JSONL_HEADERS.get(agent, lambda r: None)(record)
        if header:
            session, cwd = header.session or session, header.cwd
            if not sal.cwd_in_scope(cwd, options):
                return []
        if agent == "claude":
            cwd = cwd or record.get("cwd")
        events.extend(Event(agent, session, cwd, record.get("timestamp"), skill, trigger)
                      for skill, trigger in DETECTORS[agent](record))
    if agent == "claude" and not sal.cwd_in_scope(cwd, options):
        return []
    return dedupe_reads(events)


def jsonl_paths(agent: str, roots, options) -> Iterator[Path]:
    if agent == "claude":
        for root in (roots.claude_projects, roots.claude_archive):
            yield from sal.claude_candidate_paths(root, options)
        return
    root = {"codex": roots.codex_sessions, "droid": roots.droid_sessions,
            "pi": roots.pi_sessions}[agent]
    if root.is_dir():
        yield from (p for p in root.rglob("*.jsonl") if sal.recent_enough(p, options.cutoff))


def opencode_events(roots, options) -> list[Event]:
    if not roots.opencode_db.is_file():
        return []
    connection = sal.open_opencode(roots.opencode_db)
    try:
        sessions = {
            row["id"]: row["directory"]
            for row in connection.execute("SELECT id, directory, time_updated FROM session")
            if (options.cutoff is None or row["time_updated"] / 1000 >= options.cutoff)
            and sal.cwd_in_scope(row["directory"], options)
        }
        events = []
        for row in connection.execute(
            "SELECT m.session_id AS sid, p.data AS data, p.time_created AS created "
            "FROM part AS p JOIN message AS m ON p.message_id = m.id "
            "WHERE p.data LIKE '%\"tool\":\"skill\"%'"
        ):
            if row["sid"] not in sessions:
                continue
            try:
                part = json.loads(row["data"])
            except json.JSONDecodeError:
                continue
            events.extend(Event("opencode", row["sid"], sessions[row["sid"]],
                                sal.iso_from_millis(row["created"]), skill, trigger)
                          for skill, trigger in opencode_skills(part))
        return events
    finally:
        connection.close()


def collect(agents: Iterable[str], roots, options) -> tuple[list[Event], list[str]]:
    events: list[Event] = []
    missing: list[str] = []
    for agent in agents:
        if agent == "opencode":
            if not roots.opencode_db.is_file():
                missing.append(agent)
            events.extend(opencode_events(roots, options))
            continue
        paths = list(jsonl_paths(agent, roots, options))
        if not paths and agent != "claude" and not {
            "codex": roots.codex_sessions, "droid": roots.droid_sessions, "pi": roots.pi_sessions
        }[agent].is_dir():
            missing.append(agent)
        by_session: dict[str, list[Event]] = {}
        for path in paths:
            found = jsonl_events(agent, path, options)
            # The Claude archive can hold a second copy of a live session; keep the fuller one.
            if found and len(found) > len(by_session.get(found[0].session, [])):
                by_session[found[0].session] = found
        events.extend(e for found in by_session.values() for e in found)
    return events, missing


def is_automation(cwd: str | None) -> bool:
    return bool(cwd and AUTOMATION_CWD.search(cwd))


def summarize(events: list[Event], agents: list[str]) -> list[dict]:
    rows: dict[str, dict] = defaultdict(lambda: {
        "invocations": 0, "sessions": set(), USER: 0, MODEL: 0,
        "by_agent": {a: set() for a in agents}, "last_used": None,
    })
    for e in events:
        row = rows[e.skill]
        row["invocations"] += 1
        row[e.trigger] += 1
        row["sessions"].add((e.agent, e.session))
        row["by_agent"][e.agent].add(e.session)
        if e.timestamp and (row["last_used"] is None or e.timestamp > row["last_used"]):
            row["last_used"] = e.timestamp
    return sorted(
        ({"skill": skill, "sessions": len(r["sessions"]), "invocations": r["invocations"],
          "user": r[USER], "model": r[MODEL],
          "by_agent": {a: len(s) for a, s in r["by_agent"].items()},
          "last_used": (r["last_used"] or "")[:10]}
         for skill, r in rows.items()),
        key=lambda r: (-r["sessions"], -r["invocations"], r["skill"]),
    )


def inventory(repo: Path) -> list[str]:
    dirs = [repo / "loadout/skills", repo / ".claude/skills"]
    return sorted({p.parent.name for d in dirs if d.is_dir() for p in d.glob("*/SKILL.md")})


def render_text(rows: list[dict], agents: list[str], unused: list[str], header: str) -> str:
    lines = [header, ""]
    if rows:
        width = max(len("skill"), *(len(r["skill"]) for r in rows))
        cols = "  ".join(f"{a:>8}" for a in agents)
        lines.append(f"{'skill':<{width}}  {'sessions':>8}  {'invoked':>7}  {'user':>5}  "
                     f"{'model':>5}  {cols}  last used")
        for r in rows:
            per = "  ".join(f"{r['by_agent'][a] or '':>8}" for a in agents)
            lines.append(f"{r['skill']:<{width}}  {r['sessions']:>8}  {r['invocations']:>7}  "
                         f"{r['user'] or '':>5}  {r['model'] or '':>5}  {per}  {r['last_used']}")
    else:
        lines.append("No skill invocations found.")
    if unused:
        lines += ["", f"Unused in this window ({len(unused)}): " + ", ".join(unused)]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="skill_usage.py",
        description="Count skill invocations across agent session logs. Per-agent columns "
                    "count sessions; 'invoked' counts invocations.")
    for agent in AGENTS:
        p.add_argument(f"--{agent}", action="store_true", help=f"include {agent} sessions")
    p.add_argument("--days", type=float, default=30,
                   help="only sessions updated in the last N days (default 30; 0 = all time)")
    p.add_argument("--scope", choices=("siblings", "current", "all"), default="all",
                   help="project scope (default: all)")
    p.add_argument("--app", help="only sessions whose cwd contains this substring")
    p.add_argument("--skill", help="list the sessions that used this one skill")
    p.add_argument("--include-automation", action="store_true",
                   help="keep sessions run from temp or .sandbox directories (evals, demos)")
    p.add_argument("--format", choices=("text", "json"), default="text")
    return p


def main(argv: list[str] | None = None, roots=None, now: float | None = None) -> int:
    args = build_parser().parse_args(argv)
    agents = [a for a in AGENTS if getattr(args, a)] or list(AGENTS)
    now = time.time() if now is None else now
    options = sal.SearchOptions(
        cwd=os.getcwd(), scope=args.scope, app=args.app,
        cutoff=now - args.days * 86400 if args.days else None,
        context=0, max_snippets=0,
    )
    events, missing = collect(agents, roots or sal.Roots.from_environment(), options)
    skipped = set() if args.include_automation else {
        (e.agent, e.session) for e in events if is_automation(e.cwd)}
    events = [e for e in events if (e.agent, e.session) not in skipped]
    window = f"last {args.days:g} days" if args.days else "all time"
    header = f"Skill usage, {window}, scope {args.app or args.scope}, agents: {', '.join(agents)}"
    if skipped:
        header += f"\nExcluded {len(skipped)} automated session(s) (--include-automation keeps them)"
    if missing:
        header += f"\nIncomplete: no session store for {', '.join(missing)}"

    if args.skill:
        hits = sorted((e for e in events if e.skill == args.skill),
                      key=lambda e: e.timestamp or "", reverse=True)
        if args.format == "json":
            print(json.dumps([asdict(e) for e in hits], indent=2))
        else:
            print(header + f"\n\n{args.skill}: {len(hits)} invocation(s)")
            print("\n".join(f"{(e.timestamp or '')[:16]}  {e.agent}:{e.session}  "
                            f"{e.trigger:<5}  {e.cwd or ''}" for e in hits))
        return 0

    rows = summarize(events, agents)
    used = {r["skill"] for r in rows}
    unused = [s for s in inventory(REPO) if s not in used]
    if args.format == "json":
        print(json.dumps({"window_days": args.days or None, "agents": agents,
                          "incomplete": missing, "skills": rows, "unused": unused}, indent=2))
    else:
        print(render_text(rows, agents, unused, header))
    return 0


if __name__ == "__main__":
    sys.exit(main())
