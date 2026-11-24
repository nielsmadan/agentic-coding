from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("nono-audit")
LOADER = importlib.machinery.SourceFileLoader("nono_audit", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
nono_audit = importlib.util.module_from_spec(SPEC)
sys.modules[LOADER.name] = nono_audit
LOADER.exec_module(nono_audit)


class ProfileLinkTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.sources = self.root / "repo" / "nono"
        self.installed = self.root / "profiles"
        self.sources.mkdir(parents=True)
        self.installed.mkdir()
        (self.sources / "codex-local.json").write_text("{}")

    def test_accepts_a_link_to_the_repo_profile(self):
        (self.installed / "codex-local.json").symlink_to(self.sources / "codex-local.json")

        self.assertEqual(nono_audit.profile_link_errors(self.installed, self.sources), [])

    def test_flags_a_profile_nono_saved_over_the_link(self):
        (self.installed / "codex-local.json").write_text('{"filesystem": {"allow_file": ["/map.md"]}}')

        errors = nono_audit.profile_link_errors(self.installed, self.sources)

        self.assertEqual(len(errors), 1)
        self.assertIn("codex-local.json is not a symlink into", errors[0])

    def test_flags_a_link_to_another_file(self):
        (self.root / "elsewhere.json").write_text("{}")
        (self.installed / "codex-local.json").symlink_to(self.root / "elsewhere.json")

        errors = nono_audit.profile_link_errors(self.installed, self.sources)

        self.assertIn("codex-local.json is not a symlink into", errors[0])

    def test_skips_a_machine_without_a_profiles_dir(self):
        self.assertEqual(nono_audit.profile_link_errors(self.root / "absent", self.sources), [])


if __name__ == "__main__":
    unittest.main()
