import json
import tempfile
import unittest
from pathlib import Path

from codex import sync_superpowers


class SyncSuperpowersTests(unittest.TestCase):
    def test_makes_every_installed_skill_explicit_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            plugin = cache / "openai-curated-remote" / "superpowers" / "6.2.0"
            (plugin / ".codex-plugin").mkdir(parents=True)
            (plugin / ".codex-plugin" / "plugin.json").write_text(
                json.dumps({"name": "superpowers", "version": "6.2.0"})
            )

            interface_only = plugin / "skills" / "brainstorming"
            interface_only.mkdir(parents=True)
            (interface_only / "SKILL.md").write_text("# Brainstorming\n")
            (interface_only / "agents").mkdir()
            (interface_only / "agents" / "openai.yaml").write_text(
                'interface:\n  display_name: "Brainstorming"\n'
            )

            existing_policy = plugin / "skills" / "writing-plans"
            existing_policy.mkdir(parents=True)
            (existing_policy / "SKILL.md").write_text("# Writing Plans\n")
            (existing_policy / "agents").mkdir()
            (existing_policy / "agents" / "openai.yaml").write_text(
                "policy:\n"
                "  allow_implicit_invocation: true\n"
                "  retain_this_setting: true\n"
            )

            missing_metadata = plugin / "skills" / "verification"
            missing_metadata.mkdir(parents=True)
            (missing_metadata / "SKILL.md").write_text("# Verification\n")

            sync_superpowers.reconcile(cache)

            self.assertEqual(
                (interface_only / "agents" / "openai.yaml").read_text(),
                'interface:\n'
                '  display_name: "Brainstorming"\n'
                "\n"
                "policy:\n"
                "  allow_implicit_invocation: false\n",
            )
            self.assertEqual(
                (existing_policy / "agents" / "openai.yaml").read_text(),
                "policy:\n"
                "  allow_implicit_invocation: false\n"
                "  retain_this_setting: true\n",
            )
            self.assertEqual(
                (missing_metadata / "agents" / "openai.yaml").read_text(),
                "policy:\n  allow_implicit_invocation: false\n",
            )


if __name__ == "__main__":
    unittest.main()
