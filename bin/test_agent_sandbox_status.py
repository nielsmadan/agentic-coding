from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import subprocess
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("agent-sandbox-status")
LOADER = importlib.machinery.SourceFileLoader("agent_sandbox_status", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
status = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(status)


class StatusNoteTests(unittest.TestCase):
    def test_sandboxed_names_the_profile(self):
        note = status.status_note({"AGENT_SANDBOX": "1", "AGENT_SANDBOX_PROFILE": "codex-local"})
        self.assertIn("INSIDE the nono sandbox (profile `codex-local`)", note)

    def test_sandboxed_without_profile_says_unknown(self):
        note = status.status_note({"AGENT_SANDBOX": "1"})
        self.assertIn("(profile `unknown`)", note)

    def test_no_marker_is_unsandboxed(self):
        self.assertIn("NOT running under nono", status.status_note({}))

    def test_other_marker_values_are_unsandboxed(self):
        self.assertIn("NOT running under nono", status.status_note({"AGENT_SANDBOX": "0"}))

    def test_cli_prints_the_note_from_the_environment(self):
        env = {**os.environ, "AGENT_SANDBOX": "1", "AGENT_SANDBOX_PROFILE": "pi-local"}
        result = subprocess.run(
            [str(MODULE_PATH)], env=env, capture_output=True, text=True, check=True
        )
        self.assertEqual(result.stdout, status.status_note(env) + "\n")


class HookOutputTests(unittest.TestCase):
    def test_cursor_gets_the_note_as_additional_context(self):
        env = {"AGENT_HARNESS": "cursor", "AGENT_SANDBOX": "1", "AGENT_SANDBOX_PROFILE": "cursor-local"}
        self.assertEqual(
            json.loads(status.hook_output(env)), {"additional_context": status.status_note(env)}
        )

    def test_devin_gets_the_note_as_session_start_context(self):
        env = {"AGENT_HARNESS": "devin", "AGENT_SANDBOX": "1", "AGENT_SANDBOX_PROFILE": "devin-local"}
        self.assertEqual(
            json.loads(status.hook_output(env)),
            {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": status.status_note(env)}},
        )

    def test_other_harnesses_get_the_plain_note(self):
        env = {"AGENT_HARNESS": "claude", "AGENT_SANDBOX": "1"}
        self.assertEqual(status.hook_output(env), status.status_note(env))


if __name__ == "__main__":
    unittest.main()
