import os
from pathlib import Path
import pty
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SHIMS = ROOT / "bin" / "rl-launch"


class RlLaunchTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        home = Path(self.temporary.name)
        (home / ".airc").write_text(
            "for agent in claude codex droid opencode pi; do\n"
            "  functions[$agent]='print -r -- wrapped $0 \"$@\"'\n"
            "done\n"
        )
        real = home / "bin"
        real.mkdir()
        for agent in ("claude", "codex", "droid", "opencode", "pi"):
            binary = real / agent
            binary.write_text(f'#!/bin/sh\nprintf "%s\\n" "real {agent} $*"\n')
            binary.chmod(0o755)
        self.environment = dict(
            os.environ, HOME=str(home), PATH=f"{SHIMS}:{real}:/usr/bin:/bin"
        )
        self.environment.pop("AGENT_SANDBOX", None)

    def run_piped(self, agent, *args):
        result = subprocess.run(
            [str(SHIMS / agent), *args],
            env=self.environment,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def run_on_terminal(self, agent, *args):
        primary, secondary = pty.openpty()
        process = subprocess.Popen(
            [str(SHIMS / agent), *args],
            env=self.environment,
            stdin=secondary,
            stdout=secondary,
            stderr=secondary,
        )
        os.close(secondary)
        output = b""
        while chunk := self.read(primary):
            output += chunk
        os.close(primary)
        self.assertEqual(process.wait(), 0, output)
        return output.decode().strip()

    @staticmethod
    def read(descriptor):
        try:
            return os.read(descriptor, 4096)
        except OSError:
            return b""

    def test_terminal_launch_goes_through_the_wrapper(self):
        for agent in ("claude", "codex", "droid", "opencode", "pi"):
            with self.subTest(agent=agent):
                self.assertEqual(
                    self.run_on_terminal(agent, "resume", "two words"),
                    f"wrapped {agent} resume two words",
                )

    def test_captured_call_runs_the_real_binary(self):
        self.assertEqual(
            self.run_piped("codex", "exec", "two words"), "real codex exec two words"
        )

    def test_terminal_launch_inside_a_sandbox_runs_the_real_binary(self):
        self.environment["AGENT_SANDBOX"] = "1"
        self.assertEqual(
            self.run_on_terminal("codex", "resume", "id"), "real codex resume id"
        )


if __name__ == "__main__":
    unittest.main()
