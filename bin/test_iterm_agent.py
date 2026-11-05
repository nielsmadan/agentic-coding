import json
import os
import pty
import re
import runpy
import select
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent


def run_wrapper(script, terminal=True, timeout=5):
    setup = f'source "{ROOT}/.airc.d/06-iterm-agent.zsh"; source "{ROOT}/.airc.d/claude.zsh"; source "{ROOT}/.airc.d/codex.zsh"; '
    pane = str(uuid4()).upper()
    env = {
        **os.environ,
        "TERM_PROGRAM": "iTerm.app",
        "ITERM_SESSION_ID": "w0t0p0:" + pane,
        "PATH": str(ROOT / "bin") + ":" + os.environ["PATH"],
    }
    env.pop("AGENT_ITERM_LAUNCH_ACTIVE", None)
    if not terminal:
        result = subprocess.run(
            ["/bin/zsh", "-c", setup + script],
            env=env,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        return result.returncode, result.stdout
    master, slave = pty.openpty()
    process = subprocess.Popen(
        ["/bin/zsh", "-c", setup + script],
        env=env,
        stdin=slave,
        stdout=slave,
        stderr=slave,
        start_new_session=True,
    )
    os.close(slave)
    chunks = []
    deadline = time.monotonic() + timeout
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([master], [], [], remaining)[0]:
                raise TimeoutError("wrapper PTY timed out")
            try:
                chunk = os.read(master, 4096)
            except OSError:
                break
            if not chunk:
                break
            chunks.append(chunk)
        return process.wait(timeout=max(0.01, deadline - time.monotonic())), b"".join(
            chunks
        )
    finally:
        os.close(master)
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=2)
        root = Path.home() / ".local/state/iterm-agent-resume"
        for outcome in (root / "outcomes").glob("*.json"):
            if json.loads(outcome.read_text()).get("pane") == pane:
                outcome.unlink()
        (root / "launches" / (pane + ".json")).unlink(missing_ok=True)
        (root / "launches" / (pane + ".lock")).unlink(missing_ok=True)


READ_RECORD = 'print -n "RECORD:"; cat "$HOME/.local/state/iterm-agent-resume/launches/${ITERM_SESSION_ID##*:}.json"; print; print "PID:$sysparams[pid]"'


class WrapperTests(unittest.TestCase):
    def test_each_wrapper_records_recipe_pid_and_preserves_exit_status(self):
        for recipe in ("claude", "claude-raw", "clor", "codex", "codex-raw"):
            with self.subTest(recipe=recipe):
                implementation = "_" + recipe.replace("-", "_") + "_launch"
                code, output = run_wrapper(
                    f"{implementation}() {{ {READ_RECORD}; return 7; }}; {recipe}"
                )
                self.assertEqual(code, 7, output)
                data = json.loads(re.search(rb"RECORD:(\{[^\r\n]+\})", output)[1])
                self.assertEqual(data["recipe"], recipe)
                self.assertEqual(data["pid"], int(re.search(rb"PID:(\d+)", output)[1]))
                self.assertEqual(data["cwd"], os.getcwd())
                self.assertTrue(data["startedAt"])

    def test_nested_wrapper_preserves_outer_recipe(self):
        code, output = run_wrapper(
            f"_claude_launch() {{ claude-raw; }}; _claude_raw_launch() {{ {READ_RECORD}; return 0; }}; claude"
        )
        self.assertEqual(code, 0, output)
        data = json.loads(re.search(rb"RECORD:(\{[^\r\n]+\})", output)[1])
        self.assertEqual(data["recipe"], "claude")

    def test_noninteractive_calls_have_only_the_command_output(self):
        code, output = run_wrapper(
            "_claude_launch() { print OK; }; claude", terminal=False
        )
        self.assertEqual((code, output), (0, b"OK\n"))

    def test_exit_and_interrupt_forget_but_failure_and_hangup_preserve(self):
        for status in (0, 130, 7, 129, 139):
            with self.subTest(status=status):
                code, output = run_wrapper(
                    f"_claude_launch() {{ return {status}; }}; claude; result=$?; "
                    'print "RESULT:$result"; '
                    'if [[ -f "$HOME/.local/state/iterm-agent-resume/launches/${ITERM_SESSION_ID##*:}.json" ]]; then '
                    + READ_RECORD
                    + "; else print RECOVERY; fi"
                )
                self.assertEqual(code, 0, output)
                self.assertIn(f"RESULT:{status}".encode(), output)
                if status in (0, 130):
                    data = json.loads(re.search(rb"RECORD:(\{[^\r\n]+\})", output)[1])
                    self.assertIs(data["ended"], True)
                else:
                    data = json.loads(re.search(rb"RECORD:(\{[^\r\n]+\})", output)[1])
                    self.assertIs(data["ended"], False)
                    self.assertIs(data["finished"], True)

    def test_sigint_child_records_intentional_exit(self):
        code, output = run_wrapper(
            "_claude_launch() { /bin/sh -c 'kill -INT $$'; }; claude; "
            'print "RESULT:$?"; ' + READ_RECORD
        )
        self.assertEqual(code, 0, output)
        self.assertIn(b"RESULT:130", output)
        data = json.loads(re.search(rb"RECORD:(\{[^\r\n]+\})", output)[1])
        self.assertIs(data["ended"], True)

    def test_late_exit_preserves_newer_registration(self):
        helper = runpy.run_path(str(ROOT / "bin/iterm-agent-register"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pane = str(uuid4()).upper()
            first = helper["register"](
                root, pane, "claude", os.getpid(), directory, False
            )
            second = helper["register"](
                root, pane, "clor", os.getpid(), directory, False
            )
            helper["finish"](root, pane, first, 0)
            current = json.loads((root / "launches" / (pane + ".json")).read_text())
            self.assertEqual(current["token"], second)
            self.assertEqual(current["recipe"], "clor")
            outcome = json.loads((root / "outcomes" / (first + ".json")).read_text())
            self.assertIs(outcome["ended"], True)

    def test_start_and_end_wait_for_same_pane_lock(self):
        helper = runpy.run_path(str(ROOT / "bin/iterm-agent-register"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pane = str(uuid4()).upper()
            token = helper["register"](
                root, pane, "claude", os.getpid(), directory, False
            )
            script = "import runpy,sys; from pathlib import Path; h=runpy.run_path(sys.argv[1]); h['finish'](Path(sys.argv[2]),sys.argv[3],sys.argv[4],0)"
            with helper["pane_lock"](root / "launches", pane):
                child = subprocess.Popen(
                    [
                        "python3",
                        "-c",
                        script,
                        str(ROOT / "bin/iterm-agent-register"),
                        directory,
                        pane,
                        token,
                    ]
                )
                try:
                    with self.assertRaises(subprocess.TimeoutExpired):
                        child.wait(timeout=0.15)
                except BaseException:
                    child.kill()
                    child.wait(timeout=2)
                    raise
            self.assertEqual(child.wait(timeout=3), 0)
            self.assertIs(
                json.loads((root / "launches" / (pane + ".json")).read_text())["ended"],
                True,
            )

    def test_hung_wrapper_has_a_deadline(self):
        with self.assertRaises(TimeoutError):
            run_wrapper("_claude_launch() { sleep 10; }; claude", timeout=0.5)


if __name__ == "__main__":
    unittest.main()
