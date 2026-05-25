#!/usr/bin/env python3
"""Deploy a project-type config template into a target project.

Usage: python3 templates/deploy.py <type> [target-project-dir]

If target-project-dir is omitted, the current working directory is used.

Copies/merges the fragments in templates/<type>/ into the target project:
  - <type>/.mcp.json           -> <target>/.mcp.json                  (JSON merge)
  - <type>/settings.local.json -> <target>/.claude/settings.local.json (JSON merge)
  - <type>/skills/<name>/      -> <target>/.claude/skills/<name>/     (recursive copy)
                                  plus <target>/.agents/skills/<name> symlink
                                  pointing back at the .claude copy
  - <type>/instructions.md     -> appended once each to <target>/CLAUDE.md
                                  and <target>/AGENTS.md (state-gated per target)

All mechanical operations are idempotent. The instructions snippet is append-once per
(type, target-file) pair; subsequent updates flow through `aiconf sync`. State is tracked
in <target>/.aiconf/state.json (gitignored).
"""

import json
import os
import sys
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent

INSTRUCTION_TARGETS = ("CLAUDE.md", "AGENTS.md")


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def load_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        fail(f"{path} is not valid JSON: {e}")


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def union_list(existing, incoming):
    """Append incoming items not already present, preserving order."""
    result = list(existing)
    for item in incoming:
        if item not in result:
            result.append(item)
    return result


def merge_mcp_json(template, target_path):
    """Merge template mcpServers into target .mcp.json (template wins per server)."""
    target = load_json(target_path) or {}
    before = json.dumps(target, sort_keys=True)

    servers = target.setdefault("mcpServers", {})
    added, updated = [], []
    for name, spec in template.get("mcpServers", {}).items():
        if name not in servers:
            added.append(name)
        elif servers[name] != spec:
            updated.append(name)
        servers[name] = spec

    after = json.dumps(target, sort_keys=True)
    if before == after:
        print(f"  .mcp.json: unchanged")
    else:
        write_json(target_path, target)
        parts = []
        if added:
            parts.append(f"added {', '.join(added)}")
        if updated:
            parts.append(f"updated {', '.join(updated)}")
        print(f"  .mcp.json: {'; '.join(parts)}")


def merge_settings_local(template, target_path):
    """Merge enabledMcpjsonServers and permissions.* lists into settings.local.json."""
    target = load_json(target_path) or {}
    before = json.dumps(target, sort_keys=True)

    if "enabledMcpjsonServers" in template:
        target["enabledMcpjsonServers"] = union_list(
            target.get("enabledMcpjsonServers", []),
            template["enabledMcpjsonServers"],
        )

    if "permissions" in template:
        perms = target.setdefault("permissions", {})
        for key in ("allow", "deny", "ask"):
            if key in template["permissions"]:
                perms[key] = union_list(
                    perms.get(key, []), template["permissions"][key]
                )

    after = json.dumps(target, sort_keys=True)
    if before == after:
        print(f"  .claude/settings.local.json: unchanged")
    else:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(target_path, target)
        print(f"  .claude/settings.local.json: merged")


def deploy_skill(src_dir, dst_dir):
    """Copy skill files into dst_dir; return 'added', 'updated', or 'unchanged'."""
    state = "unchanged" if dst_dir.exists() else "added"
    for src in src_dir.rglob("*"):
        if not src.is_file() or src.name == ".DS_Store":
            continue
        rel = src.relative_to(src_dir)
        dst = dst_dir / rel
        src_bytes = src.read_bytes()
        if dst.exists() and dst.read_bytes() == src_bytes:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src_bytes)
        if state == "unchanged":
            state = "updated"
    return state


def ensure_agents_symlink(target, skill_name):
    """Ensure <target>/.agents/skills/<name> symlinks to ../../.claude/skills/<name>.

    Returns: 'added', 'updated', 'unchanged', or 'skipped (not a symlink)'.
    """
    link_path = target / ".agents" / "skills" / skill_name
    expected = Path("../..") / ".claude" / "skills" / skill_name

    if link_path.is_symlink():
        if Path(os.readlink(link_path)) == expected:
            return "unchanged"
        link_path.unlink()
        link_path.symlink_to(expected)
        return "updated"
    if link_path.exists():
        return "skipped (not a symlink)"
    link_path.parent.mkdir(parents=True, exist_ok=True)
    link_path.symlink_to(expected)
    return "added"


def deploy_skills(type_dir, target):
    skills_src = type_dir / "skills"
    if not skills_src.is_dir():
        return
    for skill_src in sorted(skills_src.iterdir()):
        if not skill_src.is_dir():
            continue
        name = skill_src.name
        skill_dst = target / ".claude" / "skills" / name
        copy_state = deploy_skill(skill_src, skill_dst)
        link_state = ensure_agents_symlink(target, name)
        print(f"  .claude/skills/{name}: {copy_state}; .agents/skills/{name}: {link_state}")


def deploy_instructions_snippet(type_name, type_dir, target):
    """Append <type>/instructions.md once each to CLAUDE.md and AGENTS.md.

    State at <target>/.aiconf/state.json tracks per (type, target-file) pair, so
    re-running can fill in a missing target without duplicating an existing one.
    Updates after first install flow through `aiconf sync`.
    """
    snippet_path = type_dir / "instructions.md"
    if not snippet_path.is_file():
        return

    state_path = target / ".aiconf" / "state.json"
    state = load_json(state_path) or {}
    installed = state.setdefault("snippet_installed", {})
    done = list(installed.get(type_name, []))

    snippet = snippet_path.read_text()
    if not snippet.endswith("\n"):
        snippet += "\n"

    appended_any = False
    for target_name in INSTRUCTION_TARGETS:
        if target_name in done:
            print(f"  {target_name}: skipped (already installed; use 'aiconf sync' to update)")
            continue
        target_file = target / target_name
        if target_file.exists():
            existing = target_file.read_text()
            if not existing.endswith("\n"):
                existing += "\n"
            target_file.write_text(existing + "\n" + snippet)
        else:
            target_file.write_text(snippet)
        done.append(target_name)
        appended_any = True
        print(f"  {target_name}: snippet appended")

    if appended_any:
        installed[type_name] = done
        state_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(state_path, state)


def available_types():
    return sorted(
        p.name for p in TEMPLATES_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")
    )


def main():
    if len(sys.argv) not in (2, 3):
        fail(f"usage: python3 {Path(__file__).name} <type> [target-project-dir]")

    type_name = sys.argv[1]
    target_arg = sys.argv[2] if len(sys.argv) == 3 else "."

    type_dir = TEMPLATES_DIR / type_name
    if not type_dir.is_dir():
        types = available_types()
        fail(f"unknown type '{type_name}'. available: {', '.join(types) or '(none)'}")

    target = Path(target_arg).expanduser().resolve()
    if not target.is_dir():
        fail(f"target project dir does not exist: {target}")

    print(f"deploying '{type_name}' template into {target}")

    mcp_template = load_json(type_dir / ".mcp.json")
    if mcp_template is not None:
        merge_mcp_json(mcp_template, target / ".mcp.json")

    settings_template = load_json(type_dir / "settings.local.json")
    if settings_template is not None:
        merge_settings_local(settings_template, target / ".claude" / "settings.local.json")

    deploy_skills(type_dir, target)

    deploy_instructions_snippet(type_name, type_dir, target)

    print("done")


if __name__ == "__main__":
    main()
