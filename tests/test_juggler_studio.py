from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class JugglerStudioTest(unittest.TestCase):
    def test_the_studio_copy_is_current(self):
        result = subprocess.run([str(ROOT / "bin" / "juggler-studio"), "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_the_studio_hooks_call_only_the_deployed_binary(self):
        hooks = (ROOT / "loadout" / "juggler-studio" / "hooks" / "hooklinesinker-claude.json").read_text()
        self.assertIn('"command": "/opt/bin/hooklinesinker ingest --agent claude --event SessionStart"', hooks)


if __name__ == "__main__":
    unittest.main()
