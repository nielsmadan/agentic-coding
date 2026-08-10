from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("manage.py")
SPEC = importlib.util.spec_from_file_location("permission_manage", MODULE_PATH)
manage = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(manage)


class PermissionManagerTests(unittest.TestCase):
    def test_mutate_moves_rule_between_decisions(self):
        rules = {
            "shell": {"allow": ["pytest"], "ask": [], "deny": []},
            "mcp": {"allow": [], "ask": [], "deny": []},
        }
        manage.mutate(rules, "deny", "shell", "pytest")
        self.assertEqual(rules["shell"]["allow"], [])
        self.assertEqual(rules["shell"]["deny"], ["pytest"])

    def test_global_edit_preserves_comments_and_moves_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "permissions.toml"
            path.write_text(
                "[shell]\n"
                "allow = [\n"
                "  # tests\n"
                '  "pytest",\n'
                "]\n"
                "deny = []\n"
                "ask = []\n"
                "\n"
                "[mcp]\n"
                "allow = []\n"
                "deny = []\n"
                "ask = []\n"
            )
            updated = manage.edit_global_source(path, "ask", "shell", "pytest")
            path.write_text(updated)
            parsed = tomllib.loads(updated)
            self.assertIn("# tests", updated)
            self.assertEqual(parsed["shell"]["allow"], [])
            self.assertEqual(parsed["shell"]["ask"], ["pytest"])

    def test_local_executable_resolution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / ".venv" / "bin" / "pytest"
            executable.parent.mkdir(parents=True)
            executable.write_text("#!/bin/sh\n")
            executable.chmod(0o755)
            target, resolved = manage.normalize_shell("pytest", "local", root)
            self.assertEqual(target, ".venv/bin/pytest")
            self.assertEqual(resolved, ".venv/bin/pytest")

    def test_rejects_nonportable_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                manage.normalize_shell("pytest | tee out", "local", Path(directory))

    def test_local_rule_cannot_weaken_global_rule(self):
        rules = {
            "shell": {"allow": [], "ask": [], "deny": ["git push"]},
            "mcp": {"allow": [], "ask": [], "deny": []},
        }
        with self.assertRaises(ValueError):
            manage.prevent_global_weakening(rules, "allow", "shell", "git")

    def test_local_render_preserves_unrelated_settings_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as project_dir, tempfile.TemporaryDirectory() as home_dir:
            root = Path(project_dir)
            home = Path(home_dir)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            claude = root / ".claude" / "settings.local.json"
            claude.parent.mkdir(parents=True)
            claude.write_text(
                json.dumps(
                    {
                        "permissions": {"allow": ["WebFetch(domain:example.com)"]},
                        "sandbox": {"enabled": False},
                    }
                )
            )
            codex_path = root / ".codex" / "config.toml"
            codex_path.parent.mkdir(parents=True)
            codex_path.write_text(
                '[mcp_servers.jina]\nurl = "https://mcp.jina.ai/v1"\n'
            )

            rules = {
                "shell": {"allow": [".venv/bin/pytest"], "ask": [], "deny": []},
                "mcp": {"allow": ["jina/*"], "ask": [], "deny": []},
            }
            manage.render_local(root, home, rules, False)
            first = claude.read_text()
            manage.render_local(root, home, rules, False)
            self.assertEqual(first, claude.read_text())

            settings = json.loads(first)
            self.assertFalse(settings["sandbox"]["enabled"])
            self.assertIn("WebFetch(domain:example.com)", settings["permissions"]["allow"])
            self.assertIn("Bash(.venv/bin/pytest:*)", settings["permissions"]["allow"])
            self.assertIn("mcp__jina__*", settings["permissions"]["allow"])

            with (root / ".codex" / "config.toml").open("rb") as file:
                codex = tomllib.load(file)
            self.assertEqual(
                codex["mcp_servers"]["jina"]["default_tools_approval_mode"],
                "approve",
            )
            self.assertEqual(
                codex["mcp_servers"]["jina"]["url"],
                "https://mcp.jina.ai/v1",
            )
            opencode = json.loads((root / "opencode.json").read_text())
            self.assertEqual(opencode["permission"]["jina_*"], "allow")
            pi = json.loads(
                (
                    root
                    / ".pi"
                    / "extensions"
                    / "pi-permission-system"
                    / "config.json"
                ).read_text()
            )
            self.assertEqual(pi["permission"]["mcp"]["jina_*"], "allow")
            self.assertEqual(
                pi["permission"]["mcp"]["mcp_server_jina"], "allow"
            )
            self.assertEqual(
                pi["permission"]["mcp"]["mcp_connect_jina"], "allow"
            )
            self.assertNotIn("jina/*", pi["permission"]["mcp"])

            empty = {
                "shell": {"allow": [], "ask": [], "deny": []},
                "mcp": {"allow": [], "ask": [], "deny": []},
            }
            manage.render_local(root, home, empty, False)
            with codex_path.open("rb") as file:
                codex = tomllib.load(file)
            self.assertEqual(
                codex["mcp_servers"]["jina"],
                {"url": "https://mcp.jina.ai/v1"},
            )

    def test_mcp_normalization(self):
        self.assertEqual(manage.normalize_mcp("jina"), "jina/*")
        self.assertEqual(manage.normalize_mcp("jina/read_url"), "jina/read_url")


if __name__ == "__main__":
    unittest.main()
