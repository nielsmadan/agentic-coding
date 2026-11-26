from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import json
import subprocess
import threading
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin" / "codex-statusline"
loader = SourceFileLoader("codex_statusline", str(SCRIPT))
statusline = module_from_spec(spec_from_loader(loader.name, loader))
loader.exec_module(statusline)


class GatedRender:
    def __init__(self):
        self.calls = []
        self.gates = {}

    def gate(self, key):
        self.gates[key] = threading.Event()
        return self.gates[key]

    def __call__(self, key, _minute):
        self.calls.append(key)
        if key in self.gates:
            self.gates[key].wait(5)
        if key == "broken":
            raise subprocess.CalledProcessError(1, "statusline.sh")
        return f"tree {key}"


def wait_until(predicate):
    deadline = time.monotonic() + 5
    while not predicate():
        if time.monotonic() > deadline:
            raise AssertionError("condition not reached")
        time.sleep(0.01)


def state(thread="t1", context=42):
    return {
        "thread": {
            "id": thread,
            "model": {"id": "gpt-test", "reasoning_level": "high"},
            "workspace": {"cwd": str(ROOT)},
            "usage": {"context": {"used_percentage": context}},
        },
        "account": {"rate_limits": []},
    }


class FootersTest(unittest.TestCase):
    def test_the_first_read_waits_for_its_render(self):
        footers = statusline.Footers(GatedRender())

        self.assertEqual(footers.read("t1", ("a", 0), 5), "tree a")

    def test_a_slow_render_does_not_hold_up_a_read(self):
        render = GatedRender()
        footers = statusline.Footers(render)
        footers.read("t1", ("a", 0), 5)
        gate = render.gate("b")

        started = time.monotonic()
        tree = footers.read("t1", ("b", 0), 5)

        self.assertEqual(tree, "tree a")
        self.assertLess(time.monotonic() - started, 0.2)
        gate.set()
        wait_until(lambda: footers.read("t1", ("b", 0), 0) == "tree b")

    def test_an_unchanged_key_reuses_the_render(self):
        render = GatedRender()
        footers = statusline.Footers(render)
        footers.read("t1", ("a", 0), 5)
        footers.read("t1", ("a", 0), 5)

        self.assertEqual(render.calls, ["a"])

    def test_each_thread_gets_its_own_footer(self):
        render = GatedRender()
        footers = statusline.Footers(render)
        footers.read("t1", ("a", 0), 5)

        self.assertEqual(footers.read("t2", ("b", 0), 5), "tree b")
        self.assertEqual(footers.read("t1", ("a", 0), 5), "tree a")

    def test_a_failed_render_keeps_the_last_footer(self):
        render = GatedRender()
        footers = statusline.Footers(render)
        footers.read("t1", ("a", 0), 5)

        footers.read("t1", ("broken", 0), 0)
        wait_until(lambda: render.calls == ["a", "broken"])

        self.assertEqual(footers.read("t1", ("broken", 0), 0), "tree a")


class ServerTest(unittest.TestCase):
    def test_a_read_returns_the_rendered_footer(self):
        server = subprocess.Popen(
            [str(SCRIPT)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {
                "uri": statusline.URI,
                "_meta": {statusline.STATE_KEY: state()},
            },
        }
        try:
            reply, _ = server.communicate(json.dumps(request) + "\n", timeout=10)
        finally:
            server.kill()

        tree = json.loads(json.loads(reply)["result"]["contents"][0]["text"])
        self.assertEqual(tree["type"], "row")
        self.assertIn("CX", json.dumps(tree["children"][0]))


if __name__ == "__main__":
    unittest.main()
