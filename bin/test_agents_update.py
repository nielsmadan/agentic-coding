from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("agents-update")
LOADER = importlib.machinery.SourceFileLoader("agents_update", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
agents_update = importlib.util.module_from_spec(SPEC)
sys.modules[LOADER.name] = agents_update
LOADER.exec_module(agents_update)


class AgentsUpdateTests(unittest.TestCase):
    def test_selects_every_agent_when_none_are_named(self):
        available = agents_update.agents(Path("/home/u"))

        chosen = agents_update.select(available, [])

        self.assertEqual([agent.name for agent in chosen], ["claude", "codex", "opencode", "pi", "droid"])

    def test_selects_named_agents_in_canonical_order(self):
        available = agents_update.agents(Path("/home/u"))

        chosen = agents_update.select(available, ["droid", "pi"])

        self.assertEqual([agent.name for agent in chosen], ["pi", "droid"])

    def test_rejects_an_unknown_agent_name(self):
        available = agents_update.agents(Path("/home/u"))

        with self.assertRaisesRegex(ValueError, "unknown agent\\(s\\): gemini"):
            agents_update.select(available, ["gemini"])

    def test_updates_pi_through_mise(self):
        pi = next(agent for agent in agents_update.agents(Path("/home/u")) if agent.name == "pi")

        self.assertEqual(pi.update, ("mise", "upgrade", "npm:@earendil-works/pi-coding-agent"))

    def test_calls_binaries_by_path_to_bypass_the_sandbox_wrappers(self):
        droid = next(agent for agent in agents_update.agents(Path("/home/u")) if agent.name == "droid")

        self.assertEqual(droid.update, ("/home/u/.local/bin/droid", "update"))

    def test_refuses_inside_the_agent_sandbox(self):
        self.assertIn("own terminal", agents_update.sandbox_refusal({"AGENT_SANDBOX": "1"}))

    def test_runs_outside_the_agent_sandbox(self):
        self.assertIsNone(agents_update.sandbox_refusal({}))


if __name__ == "__main__":
    unittest.main()
