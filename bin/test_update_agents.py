from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("update-agents")
LOADER = importlib.machinery.SourceFileLoader("update_agents", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
update_agents = importlib.util.module_from_spec(SPEC)
sys.modules[LOADER.name] = update_agents
LOADER.exec_module(update_agents)


class AgentsUpdateTests(unittest.TestCase):
    def test_selects_every_agent_when_none_are_named(self):
        available = update_agents.agents(Path("/home/u"))

        chosen = update_agents.select(available, [])

        self.assertEqual([agent.name for agent in chosen], ["claude", "codex", "opencode", "pi", "droid", "cursor"])

    def test_selects_named_agents_in_canonical_order(self):
        available = update_agents.agents(Path("/home/u"))

        chosen = update_agents.select(available, ["droid", "pi"])

        self.assertEqual([agent.name for agent in chosen], ["pi", "droid"])

    def test_rejects_an_unknown_agent_name(self):
        available = update_agents.agents(Path("/home/u"))

        with self.assertRaisesRegex(ValueError, "unknown agent\\(s\\): gemini"):
            update_agents.select(available, ["gemini"])

    def test_updates_pi_through_mise(self):
        pi = next(agent for agent in update_agents.agents(Path("/home/u")) if agent.name == "pi")

        self.assertEqual(pi.update, ("mise", "upgrade", "npm:@earendil-works/pi-coding-agent"))

    def test_calls_binaries_by_path_to_bypass_the_sandbox_wrappers(self):
        droid = next(agent for agent in update_agents.agents(Path("/home/u")) if agent.name == "droid")

        self.assertEqual(droid.update, ("/home/u/.local/bin/droid", "update"))

    def test_refuses_inside_the_agent_sandbox(self):
        self.assertIn("own terminal", update_agents.sandbox_refusal({"AGENT_SANDBOX": "1"}))

    def test_runs_outside_the_agent_sandbox(self):
        self.assertIsNone(update_agents.sandbox_refusal({}))


if __name__ == "__main__":
    unittest.main()
