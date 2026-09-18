import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProfileLaunchersTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.config = Path(self.temporary.name) / "loadout" / "config.toml"
        self.config.parent.mkdir()
        self.config.write_text('profile = "unsandboxed"\n')
        self.environment = dict(os.environ, XDG_CONFIG_HOME=self.temporary.name)
        for key in ("AGENT_FORCE_SANDBOX", "AGENT_REQUIRE_SANDBOX"):
            self.environment.pop(key, None)

    def run_shell(self, body):
        return subprocess.run(
            ["zsh", "-f", "-c", body],
            cwd=ROOT,
            env=self.environment,
            text=True,
            capture_output=True,
        )

    def test_launchers_keep_arguments_without_nono(self):
        for agent in ("claude", "codex", "opencode", "pi"):
            with self.subTest(agent=agent):
                result = self.run_shell(f'''
source .airc.d/05-sandbox.zsh
source .airc.d/{agent}.zsh
_agent_raw_dir() {{ return 1; }}
sops-exec() {{ printf '%s\\n' "$@"; }}
{agent} --version 'two words'
''')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.splitlines(),
                                 [agent, "--version", "two words"])

    def test_clor_launches_claude_with_openrouter_settings(self):
        result = self.run_shell('''
source .airc.d/05-sandbox.zsh
source .airc.d/claude.zsh
sops() { zsh -f -c "function claude { printf '%s\\n' \\"\\$ANTHROPIC_BASE_URL\\" \\"\\$@\\"; }; $3"; }
clor --print 'two words'
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            "https://openrouter.ai/api", "--model", "sonnet",
            "--permission-mode", "acceptEdits", "--print", "two words",
        ])

    def test_profile_switch_is_read_on_each_call(self):
        result = self.run_shell('''
source .airc.d/05-sandbox.zsh
_agent_unsandboxed_profile
printf '%s\\n' "$?"
printf 'profile = "autonomous"\\n' > "$XDG_CONFIG_HOME/loadout/config.toml"
_agent_unsandboxed_profile
printf '%s\\n' "$?"
''')
        self.assertEqual(result.stdout.splitlines(), ["0", "1"])

    def test_explicit_sandbox_requirements_take_precedence(self):
        for key in ("AGENT_FORCE_SANDBOX", "AGENT_REQUIRE_SANDBOX"):
            with self.subTest(key=key):
                self.environment[key] = "1"
                result = self.run_shell("source .airc.d/05-sandbox.zsh; _agent_unsandboxed_profile")
                self.assertEqual(result.returncode, 1, result.stderr)
                self.environment.pop(key)


if __name__ == "__main__":
    unittest.main()
