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


class SopsExecTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        self.store = base / "secrets.yaml"
        self.key = base / "keys.txt"
        fake_bin = base / "bin"
        fake_bin.mkdir()
        sops = fake_bin / "sops"
        sops.write_text('#!/bin/sh\nshift 2\nexec sh -c "$1"\n')
        sops.chmod(0o755)
        self.environment = dict(
            os.environ,
            PATH=f"{fake_bin}:{os.environ['PATH']}",
            SOPS_SECRETS=str(self.store),
            SOPS_AGE_KEY_FILE=str(self.key),
            AGENT_REQUIRE_SECRETS="1",
        )

    def run_sops_exec(self, *argv):
        return subprocess.run(
            [str(ROOT / "bin" / "sops-exec"), *argv],
            env=self.environment,
            text=True,
            capture_output=True,
        )

    def test_required_secrets_refuse_without_a_store(self):
        result = self.run_sops_exec("echo", "ran")
        self.assertEqual(result.returncode, 78)
        self.assertIn("refusing to run 'echo' without secrets", result.stderr)

    def test_requirement_is_not_inherited_by_the_child(self):
        self.store.write_text("")
        self.key.write_text("")
        result = self.run_sops_exec("env")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"SOPS_SECRETS={self.store}", result.stdout.splitlines())
        names = {line.split("=", 1)[0] for line in result.stdout.splitlines()}
        self.assertNotIn("AGENT_REQUIRE_SECRETS", names)

    def test_nested_call_without_a_store_runs_the_command(self):
        self.store.write_text("")
        self.key.write_text("")
        nested = f'SOPS_SECRETS=/nonexistent {ROOT / "bin" / "sops-exec"} echo nested-ran'
        result = self.run_sops_exec("sh", "-c", nested)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "nested-ran\n")


if __name__ == "__main__":
    unittest.main()
