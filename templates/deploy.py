#!/usr/bin/env python3
"""Deploy a project-type config template into a target project.

Usage: python3 templates/deploy.py <type> [target-project-dir]

If target-project-dir is omitted, the current working directory is used.

Merges the MCP half of templates/<type>/ into the target project:
  - <type>/.mcp.json           -> <target>/.mcp.json                  (JSON merge)
  - <type>/settings.local.json -> <target>/.claude/settings.local.json (JSON merge,
                                  every key except `permissions`)

Permissions, instructions and skills live in loadout/templates/<type>/ and are
rendered by `loadout sync` for every harness the project enables. They used to be
deployed here, for Claude alone. What stays is the pair loadout has no model of:
server definitions in .mcp.json, and the enabledMcpjsonServers key that switches
them on — meaningless apart, so neither moves without the other.

Both merges are idempotent.
"""

import json
import os
import sys
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent


CLAUDE_BRIDGE = "@AGENTS.md\n"


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


# loadout/templates/ is the list of project types; this directory holds only the
# MCP half, and a type with no MCP content has no directory here at all.
LOADOUT_TEMPLATES_DIR = TEMPLATES_DIR.parent / "loadout" / "templates"


def available_types():
    return sorted(
        p.name for p in LOADOUT_TEMPLATES_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")
    )


def main():
    if len(sys.argv) not in (2, 3):
        fail(f"usage: python3 {Path(__file__).name} <type> [target-project-dir]")

    type_name = sys.argv[1]
    target_arg = sys.argv[2] if len(sys.argv) == 3 else "."

    if type_name not in available_types():
        types = available_types()
        fail(f"unknown type '{type_name}'. available: {', '.join(types) or '(none)'}")

    type_dir = TEMPLATES_DIR / type_name
    if not type_dir.is_dir():
        # A known type with nothing to merge here: everything it carries is
        # permissions, instructions or skills, which `loadout sync` renders.
        print(f"'{type_name}' has no MCP fragments; declare it in loadout/config.toml and sync")
        return

    target = Path(target_arg).expanduser().resolve()
    if not target.is_dir():
        fail(f"target project dir does not exist: {target}")

    print(f"deploying '{type_name}' template into {target}")

    mcp_template = load_json(type_dir / ".mcp.json")
    if mcp_template is not None:
        merge_mcp_json(mcp_template, target / ".mcp.json")

    # Permissions, instructions and skills moved to loadout/templates/<type>/ —
    # a project declares `templates = ["<type>"]` in loadout/config.toml and
    # `loadout sync` renders them for every harness it enables, rather than for
    # Claude alone. What is left here is the MCP half: server *definitions* in
    # .mcp.json, and the enabledMcpjsonServers key that switches them on, which
    # are meaningless apart and which loadout has no model of.
    settings_template = load_json(type_dir / "settings.local.json")
    if settings_template is not None:
        mcp_only = {k: v for k, v in settings_template.items() if k != "permissions"}
        if mcp_only:
            merge_settings_local(mcp_only, target / ".claude" / "settings.local.json")

    print("done")


if __name__ == "__main__":
    main()
