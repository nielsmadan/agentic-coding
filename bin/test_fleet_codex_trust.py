from __future__ import annotations

import importlib.machinery
import importlib.util
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("fleet-codex-trust")
LOADER = importlib.machinery.SourceFileLoader("fleet_codex_trust", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
trust = importlib.util.module_from_spec(SPEC)
sys.modules[LOADER.name] = trust
LOADER.exec_module(trust)


class MissingEntriesTests(unittest.TestCase):
    def test_adds_only_clones_without_an_entry(self):
        config = '[projects."/f/repos/rc"]\ntrust_level = "untrusted"\n'

        addition = trust.missing_entries(config, [Path("/f/repos/ac"), Path("/f/repos/rc")])

        self.assertEqual(tomllib.loads(config + addition)["projects"],
                         {"/f/repos/rc": {"trust_level": "untrusted"}, "/f/repos/ac": {"trust_level": "trusted"}})


class CommandTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.repos = self.root / "repos"
        for name in ("cadet", "loadout"):
            (self.repos / name / ".git").mkdir(parents=True)
        (self.repos / "notes.txt").write_text("not a clone")
        self.config = self.root / "config.toml"
        self.config.write_text('model = "gpt-6"\n')

    def run_trust(self):
        return subprocess.run([str(MODULE_PATH), str(self.config), str(self.repos)],
                              capture_output=True, text=True, timeout=30)

    def test_trusts_each_clone_once_and_keeps_the_rest_of_the_config(self):
        self.assertEqual(self.run_trust().returncode, 0)
        self.assertEqual(self.run_trust().returncode, 0)

        parsed = tomllib.loads(self.config.read_text())
        self.assertEqual(parsed["model"], "gpt-6")
        self.assertEqual(parsed["projects"], {
            str(self.repos / "cadet"): {"trust_level": "trusted"},
            str(self.repos / "loadout"): {"trust_level": "trusted"},
        })


if __name__ == "__main__":
    unittest.main()
