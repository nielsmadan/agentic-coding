#!/usr/bin/env python3
"""Manage canonical global and project-local agent permissions.

Usage:
    aiperm allow --scope local --shell pytest
    aiperm allow --scope global --mcp jina/read_url
    aiperm remove --scope local --shell pytest
    aiperm list --scope all
    aiperm sync --scope local
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path


DECISIONS = ("allow", "ask", "deny")
MCP_TARGET = re.compile(r"^[A-Za-z0-9_.-]+/(?:\*|[A-Za-z0-9_.:/-]+)$")
UNSAFE_SHELL = re.compile(r"[|;&><`*\n]|\$\(")


def fail(message: str) -> None:
    raise ValueError(message)


def repo_root() -> Path:
    override = os.environ.get("AIPERM_REPO_ROOT")
    return Path(override).resolve() if override else Path(__file__).resolve().parent.parent


def project_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=False,
    )
    return Path(result.stdout.strip()).resolve() if result.returncode == 0 else Path.cwd().resolve()


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".aiperm-")
    try:
        with os.fdopen(fd, "w") as file:
            file.write(content)
        os.replace(temporary, path)
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


def atomic_batch(items: list[tuple[Path, str]]) -> None:
    originals = {
        path: path.read_text() if path.exists() else None
        for path, _ in items
    }
    try:
        for path, content in items:
            atomic_write(path, content)
    except BaseException:
        for path, content in originals.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                atomic_write(path, content)
        raise


def load_rules(path: Path) -> dict[str, dict[str, list[str]]]:
    if not path.exists():
        return {
            "shell": {decision: [] for decision in DECISIONS},
            "mcp": {decision: [] for decision in DECISIONS},
        }
    with path.open("rb") as file:
        data = tomllib.load(file)
    return {
        kind: {
            decision: list(data.get(kind, {}).get(decision, []))
            for decision in DECISIONS
        }
        for kind in ("shell", "mcp")
    }


def render_rules(rules: dict[str, dict[str, list[str]]]) -> str:
    lines = ["# Managed by aiperm."]
    for kind in ("shell", "mcp"):
        lines += ["", f"[{kind}]"]
        for decision in DECISIONS:
            values = ", ".join(json.dumps(value) for value in rules[kind][decision])
            lines.append(f"{decision} = [{values}]")
    return "\n".join(lines) + "\n"


def normalize_mcp(target: str) -> str:
    if "/" not in target:
        target += "/*"
    if not MCP_TARGET.fullmatch(target):
        fail("MCP targets must use server/* or server/tool syntax")
    return target


# Mirrors pi_mcp_patterns() in sync.py: Pi derives its own targets from the MCP
# call input and never sees `server/tool`.
def pi_mcp_patterns(target: str) -> list[str]:
    server, tool = target.split("/", 1)
    patterns = [f"{server}_{tool}", f"{server}:{tool}"]
    if tool == "*":
        patterns += [f"mcp_server_{server}", f"mcp_connect_{server}"]
    return patterns


def normalize_shell(target: str, scope: str, root: Path) -> tuple[str, str | None]:
    target = " ".join(target.split())
    if not target:
        fail("shell command prefix cannot be empty")
    if UNSAFE_SHELL.search(target):
        fail("portable shell rules cannot contain globs, control operators, or redirections")
    try:
        tokens = shlex.split(target)
    except ValueError as error:
        fail(f"invalid shell prefix: {error}")
    if not tokens:
        fail("shell command prefix cannot be empty")
    resolved = None
    if scope == "local" and len(tokens) == 1 and "/" not in tokens[0]:
        candidates = [
            candidate
            for candidate in (root / ".venv" / "bin" / tokens[0], root / "venv" / "bin" / tokens[0])
            if candidate.is_file() and os.access(candidate, os.X_OK)
        ]
        if len(candidates) == 1:
            resolved = str(candidates[0].relative_to(root))
            target = resolved
    return target, resolved


def mutate(rules: dict, action: str, kind: str, target: str) -> None:
    for decision in DECISIONS:
        rules[kind][decision] = [
            existing for existing in rules[kind][decision] if existing != target
        ]
    if action != "remove":
        rules[kind][action].append(target)


def overlaps(kind: str, left: str, right: str) -> bool:
    if kind == "mcp":
        left_server, left_tool = left.split("/", 1)
        right_server, right_tool = right.split("/", 1)
        return left_server == right_server and (
            left_tool == "*" or right_tool == "*" or left_tool == right_tool
        )
    left_tokens = shlex.split(left)
    right_tokens = shlex.split(right)
    shortest = min(len(left_tokens), len(right_tokens))
    return left_tokens[:shortest] == right_tokens[:shortest]


def prevent_global_weakening(
    global_rules: dict, action: str, kind: str, target: str
) -> None:
    if action == "remove":
        return
    rank = {"allow": 0, "ask": 1, "deny": 2}
    for decision in DECISIONS:
        if rank[decision] <= rank[action]:
            continue
        for existing in global_rules[kind][decision]:
            if overlaps(kind, existing, target):
                fail(
                    f"local {action} would weaken global {decision} rule {existing!r}"
                )


def find_section(lines: list[str], section: str) -> tuple[int, int]:
    start = next(
        (index for index, line in enumerate(lines) if line.strip() == f"[{section}]"),
        -1,
    )
    if start < 0:
        return -1, -1
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if lines[index].lstrip().startswith("[")
        ),
        len(lines),
    )
    return start, end


def find_array(lines: list[str], start: int, end: int, name: str) -> tuple[int, int]:
    opening = next(
        (
            index
            for index in range(start + 1, end)
            if re.match(rf"^\s*{re.escape(name)}\s*=\s*\[", lines[index])
        ),
        -1,
    )
    if opening < 0:
        return -1, -1
    closing = next(
        (index for index in range(opening, end) if lines[index].strip() == "]"),
        opening,
    )
    return opening, closing


def edit_global_source(path: Path, action: str, kind: str, target: str) -> str:
    lines = path.read_text().splitlines()
    start, end = find_section(lines, kind)
    if start < 0:
        lines += ["", f"[{kind}]"] + [f"{decision} = []" for decision in DECISIONS]
        start, end = find_section(lines, kind)

    encoded = json.dumps(target)
    for decision in DECISIONS:
        start, end = find_section(lines, kind)
        opening, closing = find_array(lines, start, end, decision)
        if opening < 0:
            lines.insert(end, f"{decision} = []")
            continue
        lines = [
            line
            for index, line in enumerate(lines)
            if not (
                opening < index < closing
                and re.match(rf"^\s*{re.escape(encoded)},?\s*$", line)
            )
        ]

    if action != "remove":
        start, end = find_section(lines, kind)
        opening, closing = find_array(lines, start, end, action)
        if opening == closing:
            lines[opening] = f"{action} = ["
            lines.insert(opening + 1, f"  {encoded},")
            lines.insert(opening + 2, "]")
        else:
            lines.insert(closing, f"  {encoded},")
    return "\n".join(lines) + "\n"


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def write_json(path: Path, data: dict) -> None:
    atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def native_mcp(target: str) -> str:
    server, tool = target.split("/", 1)
    return f"mcp__{server}__{tool}"


def local_native_rules(rules: dict) -> dict:
    result = {}
    for decision in DECISIONS:
        result[decision] = {
            "claude": [f"Bash({entry}:*)" for entry in rules["shell"][decision]]
            + [native_mcp(entry) for entry in rules["mcp"][decision]],
        }
    return result


def merge_owned_lists(config: dict, state: dict, path: tuple[str, ...], current: dict) -> dict:
    node = config
    for part in path:
        node = node.setdefault(part, {})
    key = ".".join(path)
    previous = state.get(key, {})
    for decision in DECISIONS:
        values = list(node.get(decision, []))
        values = [value for value in values if value not in previous.get(decision, [])]
        for value in current.get(decision, []):
            if value not in values:
                values.append(value)
        node[decision] = values
    state[key] = current
    return config


def merge_owned_map(config: dict, state: dict, path: tuple[str, ...], current: dict) -> dict:
    node = config
    for part in path:
        node = node.setdefault(part, {})
    key = ".".join(path)
    for old_key, old_value in state.get(key, {}).items():
        if node.get(old_key) == old_value:
            node.pop(old_key, None)
    node.update(current)
    state[key] = current
    return config


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
    fail(f"unsupported TOML value: {value!r}")


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
        for key, value in children.items():
            emit(value, path + (key,))

    emit(data, ())
    return "\n".join(lines) + "\n"


def merge_dict(base: dict, overlay: dict) -> dict:
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge_dict(base[key], value)
        elif isinstance(value, list) and isinstance(base.get(key), list):
            base[key] = list(dict.fromkeys(base[key] + value))
        else:
            base[key] = value
    return base


def remove_owned_dict(current: dict, previous: dict) -> None:
    for key, value in previous.items():
        if isinstance(value, dict) and isinstance(current.get(key), dict):
            remove_owned_dict(current[key], value)
            if not current[key]:
                current.pop(key, None)
        elif isinstance(value, list) and isinstance(current.get(key), list):
            current[key] = [item for item in current[key] if item not in value]
            if not current[key]:
                current.pop(key, None)
        elif current.get(key) == value:
            current.pop(key, None)


def codex_mcp(rules: dict) -> dict:
    servers: dict[str, dict] = {}
    for decision, mode in (("allow", "approve"), ("ask", "prompt")):
        for target in rules["mcp"][decision]:
            server, tool = target.split("/", 1)
            node = servers.setdefault(server, {})
            if tool == "*":
                node["default_tools_approval_mode"] = mode
            else:
                node.setdefault("tools", {}).setdefault(tool, {})["approval_mode"] = mode
    for target in rules["mcp"]["deny"]:
        server, tool = target.split("/", 1)
        node = servers.setdefault(server, {})
        if tool == "*":
            node["enabled"] = False
        else:
            node.setdefault("disabled_tools", []).append(tool)
    return servers


def codex_shell(rules: dict) -> str:
    modes = {"allow": "allow", "ask": "prompt", "deny": "forbidden"}
    lines = ["# GENERATED by aiperm — edit .aiconf/permissions.toml."]
    for decision in DECISIONS:
        for entry in rules["shell"][decision]:
            tokens = ", ".join(json.dumps(token) for token in shlex.split(entry))
            lines.append(
                f'prefix_rule(pattern = [{tokens}], decision = "{modes[decision]}")'
            )
    return "\n".join(lines) + "\n"


def ensure_personal(root: Path, paths: list[Path]) -> None:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-path", "info/exclude"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return
    exclude = Path(result.stdout.strip())
    if not exclude.is_absolute():
        exclude = root / exclude
    existing = exclude.read_text().splitlines() if exclude.exists() else []
    additions = []
    for path in paths:
        relative = str(path.relative_to(root))
        tracked = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--error-unmatch", "--", relative],
            capture_output=True,
            check=False,
        )
        if tracked.returncode == 0:
            fail(f"personal permission output is tracked: {relative}")
        if relative not in existing:
            additions.append(relative)
    if additions:
        content = "\n".join(existing + additions) + "\n"
        atomic_write(exclude, content)


def render_local(root: Path, home: Path, rules: dict, dry_run: bool) -> list[str]:
    state_path = root / ".aiconf" / "permissions-state.json"
    state = read_json(state_path)
    owned = state.setdefault("owned", {})
    native = local_native_rules(rules)
    paths = [
        root / ".aiconf" / "permissions.toml",
        root / ".aiconf" / "permissions-state.json",
        root / ".aiconf" / "mcp-permissions.json",
        root / ".claude" / "settings.local.json",
        root / ".codex" / "rules" / "aiconf.rules",
        root / ".codex" / "config.toml",
        root / "opencode.json",
        root / ".pi" / "extensions" / "pi-permission-system" / "config.json",
    ]
    if not dry_run:
        ensure_personal(root, paths)

    outputs: list[tuple[Path, str]] = []
    claude_path = paths[3]
    claude = merge_owned_lists(
        read_json(claude_path),
        owned.setdefault("claude", {}),
        ("permissions",),
        {decision: native[decision]["claude"] for decision in DECISIONS},
    )
    outputs.append((claude_path, json.dumps(claude, indent=2) + "\n"))
    outputs.append((paths[4], codex_shell(rules)))

    codex_path = paths[5]
    codex = {}
    if codex_path.exists():
        with codex_path.open("rb") as file:
            codex = tomllib.load(file)
    codex_state = owned.setdefault("codex_mcp", {})
    mcp_servers = codex.setdefault("mcp_servers", {})
    for server, previous in codex_state.items():
        if isinstance(mcp_servers.get(server), dict):
            remove_owned_dict(mcp_servers[server], previous)
            if not mcp_servers[server]:
                mcp_servers.pop(server, None)
    current_codex = codex_mcp(rules)
    merge_dict(mcp_servers, current_codex)
    codex_state.clear()
    codex_state.update(current_codex)
    if not mcp_servers:
        codex.pop("mcp_servers", None)
    outputs.append((codex_path, render_toml(codex)))

    opencode_path = paths[6]
    opencode = read_json(opencode_path)
    permission = opencode.setdefault("permission", {})
    bash = {"*": "ask"}
    for decision in DECISIONS:
        for entry in rules["shell"][decision]:
            bash[entry] = decision
            bash[f"{entry} *"] = decision
    opencode_state = owned.setdefault("opencode", {})
    merge_owned_map(opencode, opencode_state, ("permission", "bash"), bash)
    mcp_map = {}
    for decision in DECISIONS:
        for target in rules["mcp"][decision]:
            server, tool = target.split("/", 1)
            mcp_map[f"{server}_{tool}"] = decision
    merge_owned_map(opencode, opencode_state, ("permission",), mcp_map)
    outputs.append((opencode_path, json.dumps(opencode, indent=2) + "\n"))

    pi_path = paths[7]
    pi = read_json(pi_path)
    pi_permission = pi.setdefault("permission", {})
    pi_bash = {}
    for decision in DECISIONS:
        for entry in rules["shell"][decision]:
            pi_bash[f"{entry} *"] = decision
    pi_state = owned.setdefault("pi", {})
    merge_owned_map(pi, pi_state, ("permission", "bash"), pi_bash)
    pi_mcp = {
        pattern: decision
        for decision in DECISIONS
        for target in rules["mcp"][decision]
        for pattern in pi_mcp_patterns(target)
    }
    merge_owned_map(pi, pi_state, ("permission", "mcp"), pi_mcp)
    outputs.append((pi_path, json.dumps(pi, indent=2) + "\n"))

    policy = {decision: rules["mcp"][decision] for decision in DECISIONS}
    outputs.append((paths[2], json.dumps(policy, indent=2) + "\n"))

    pending = []

    if dry_run:
        return [str(path) for path, _ in outputs] + pending
    atomic_batch(
        [(paths[0], render_rules(rules))]
        + outputs
        + [(state_path, json.dumps(state, indent=2) + "\n")]
    )
    return [str(path) for path, _ in outputs] + pending


def run_global_sync(root: Path) -> None:
    subprocess.run(["loadout", "sync", "--root", str(root)], check=True)
    if os.environ.get("AIPERM_NO_INSTALL") != "1":
        subprocess.run([str(root / "sync.sh")], check=True)


def print_rules(label: str, rules: dict) -> None:
    print(label)
    for kind in ("shell", "mcp"):
        print(f"  {kind}:")
        for decision in DECISIONS:
            values = rules[kind][decision]
            print(f"    {decision}: {', '.join(values) if values else '(none)'}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="aiperm")
    subparsers = result.add_subparsers(dest="action", required=True)
    for action in (*DECISIONS, "remove"):
        command = subparsers.add_parser(action)
        command.add_argument("--scope", choices=("local", "global"), required=True)
        target = command.add_mutually_exclusive_group(required=True)
        target.add_argument("--shell", nargs="+")
        target.add_argument("--mcp")
        command.add_argument("--dry-run", action="store_true")
    listing = subparsers.add_parser("list")
    listing.add_argument("--scope", choices=("local", "global", "all"), default="all")
    syncing = subparsers.add_parser("sync")
    syncing.add_argument("--scope", choices=("local", "global", "all"), required=True)
    syncing.add_argument("--dry-run", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    root = repo_root()
    project = project_root()
    global_path = root / "permissions" / "permissions.toml"
    local_path = project / ".aiconf" / "permissions.toml"
    try:
        if args.action == "list":
            if args.scope in ("global", "all"):
                print_rules("global", load_rules(global_path))
            if args.scope in ("local", "all"):
                print_rules(f"local ({project})", load_rules(local_path))
            return 0

        if args.action == "sync":
            scopes = ("local", "global") if args.scope == "all" else (args.scope,)
            if "global" in scopes:
                if args.dry_run:
                    print("would regenerate and install global permissions")
                else:
                    run_global_sync(root)
            if "local" in scopes:
                for output in render_local(
                    project,
                    Path(os.environ.get("AIPERM_HOME", str(Path.home()))),
                    load_rules(local_path),
                    args.dry_run,
                ):
                    print(output)
            return 0

        kind = "shell" if args.shell else "mcp"
        target = (
            normalize_shell(" ".join(args.shell), args.scope, project)[0]
            if kind == "shell"
            else normalize_mcp(args.mcp)
        )
        print(f"{args.action} {kind} {target} ({args.scope})")
        if args.scope == "global":
            content = edit_global_source(global_path, args.action, kind, target)
            if args.dry_run:
                print("would update permissions/permissions.toml and regenerate global config")
                return 0
            original = global_path.read_text()
            atomic_write(global_path, content)
            try:
                run_global_sync(root)
            except BaseException:
                atomic_write(global_path, original)
                subprocess.run(
                    ["loadout", "sync", "--root", str(root)],
                    check=False,
                )
                raise
        else:
            rules = load_rules(local_path)
            prevent_global_weakening(
                load_rules(global_path), args.action, kind, target
            )
            mutate(rules, args.action, kind, target)
            for output in render_local(
                project,
                Path(os.environ.get("AIPERM_HOME", str(Path.home()))),
                rules,
                args.dry_run,
            ):
                print(output)
        return 0
    except (OSError, ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError) as error:
        print(f"aiperm: {error}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as error:
        print(f"aiperm: command failed with exit {error.returncode}", file=sys.stderr)
        return error.returncode


if __name__ == "__main__":
    raise SystemExit(main())
