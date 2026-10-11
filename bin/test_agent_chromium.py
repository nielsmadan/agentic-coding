from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import io
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).with_name("agent-chromium")
LOADER = importlib.machinery.SourceFileLoader("agent_chromium", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
ac = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(ac)

TARGETS = [
    {"id": "w1", "type": "service_worker", "title": "sw", "url": "https://www.reddit.com/sw.js"},
    {"id": "p1", "type": "page", "title": "Example Domain", "url": "https://example.com/"},
    {"id": "p2", "type": "page", "title": "Prove your humanity", "url": "https://www.reddit.com/r/x/"},
]


class AgentChromiumTests(unittest.TestCase):
    def test_launch_argv_uses_dedicated_profile_and_loopback_port(self):
        argv = ac.launch_argv("/bin/chromium", Path("/p"), 9333, "https://www.reddit.com/login/")

        self.assertEqual(argv[0], "/bin/chromium")
        self.assertIn("--user-data-dir=/p", argv)
        self.assertIn("--remote-debugging-port=9333", argv)
        self.assertIn("--remote-debugging-address=127.0.0.1", argv)
        self.assertEqual(argv[-1], "https://www.reddit.com/login/")

    def test_pick_target_matches_url_or_title_among_pages_only(self):
        self.assertEqual(ac.pick_target(TARGETS, "reddit")["id"], "p2")
        self.assertEqual(ac.pick_target(TARGETS, "HUMANITY")["id"], "p2")
        self.assertEqual(ac.pick_target(TARGETS, None)["id"], "p1")
        self.assertEqual(ac.pick_target(TARGETS, "p2")["title"], "Prove your humanity")
        self.assertIsNone(ac.pick_target(TARGETS, "github"))

    def test_start_reports_endpoint_without_launching_when_already_up(self):
        out = io.StringIO()
        with mock.patch.object(ac, "is_up", return_value=True), \
                mock.patch.object(ac.subprocess, "Popen") as popen, redirect_stdout(out):
            code = ac.cmd_start(argparse.Namespace(port=9222, url=None))

        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), "http://127.0.0.1:9222\n")
        popen.assert_not_called()

    def test_start_inside_sandbox_refuses_and_names_the_user_command(self):
        err = io.StringIO()
        with mock.patch.object(ac, "is_up", return_value=False), \
                mock.patch.dict(os.environ, {"AGENT_SANDBOX": "1"}), \
                mock.patch.object(ac.subprocess, "Popen") as popen, redirect_stderr(err):
            code = ac.cmd_start(argparse.Namespace(port=9222, url=None))

        self.assertEqual(code, ac.EX_CONFIG)
        self.assertIn("`agent-chromium start` in their own terminal", err.getvalue())
        popen.assert_not_called()


def server_frame(payload: bytes, opcode: int = 0x1, fin: bool = True) -> bytes:
    head = (0x80 if fin else 0) | opcode
    n = len(payload)
    if n < 126:
        return bytes([head, n]) + payload
    return bytes([head, 126]) + n.to_bytes(2, "big") + payload


class FakeCdp:
    def __init__(self, value="page text", exception=None):
        self.calls = []
        self.value = value
        self.exception = exception
        self.closed = False

    def call(self, method, params=None, session=None):
        self.calls.append((method, params))
        if method == "Target.createTarget":
            return {"targetId": "T1"}
        if method == "Target.attachToTarget":
            return {"sessionId": "S1"}
        if method == "Runtime.evaluate":
            if params["expression"] == ac.LOADED:
                return {"result": {"value": True}}
            if self.exception:
                return {"result": {}, "exceptionDetails": {"exception": {"description": self.exception}}}
            return {"result": {"value": self.value}}
        return {}

    def close(self):
        self.closed = True

    def methods(self):
        return [m for m, _ in self.calls]


def read_opts(**kw):
    return argparse.Namespace(**{"port": 9222, "url": "https://www.seriouseats.com/x",
                                 "expression": "document.body.innerText", "timeout": 5,
                                 "keep": False, **kw})


class CdpWireTests(unittest.TestCase):
    def test_ws_frame_masks_payload_and_encodes_each_length_class(self):
        mask = b"\x01\x02\x03\x04"
        for size, header_len in ((5, 2), (300, 4), (70000, 10)):
            payload = bytes(range(256)) * (size // 256) + bytes(size % 256)
            frame = ac.ws_frame(payload, mask)
            body = frame[header_len + 4:]

            self.assertEqual(frame[0], 0x81)
            self.assertTrue(frame[1] & 0x80)
            self.assertEqual(frame[header_len:header_len + 4], mask)
            self.assertEqual(bytes(b ^ mask[i % 4] for i, b in enumerate(body)), payload)

    def test_read_frame_decodes_extended_length(self):
        payload = b"x" * 300
        self.assertEqual(ac.read_frame(io.BytesIO(server_frame(payload))), (True, 0x1, payload))

    def test_read_frame_raises_on_truncated_frame(self):
        with self.assertRaises(ConnectionError):
            ac.read_frame(io.BytesIO(server_frame(b"abcdef")[:4]))

    def test_recv_joins_fragments_and_answers_ping(self):
        cdp = ac.Cdp.__new__(ac.Cdp)
        cdp.sock = mock.Mock()
        cdp.rfile = io.BytesIO(server_frame(b'{"id": 1, ', fin=False)
                               + server_frame(b"hi", opcode=0x9)
                               + server_frame(b'"result": {}}', opcode=0x0))

        self.assertEqual(cdp.recv(), {"id": 1, "result": {}})
        pong = cdp.sock.sendall.call_args.args[0]
        self.assertEqual(pong[0], 0x8A)


class ReadTests(unittest.TestCase):
    def run_read(self, cdp, **kw):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(ac, "is_up", return_value=True), \
                mock.patch.object(ac, "get_json", return_value={"webSocketDebuggerUrl": "ws://x/y"}), \
                mock.patch.object(ac, "Cdp", return_value=cdp), \
                redirect_stdout(out), redirect_stderr(err):
            code = ac.cmd_read(read_opts(**kw))
        return code, out.getvalue(), err.getvalue()

    def test_read_opens_background_tab_prints_value_and_closes_it(self):
        cdp = FakeCdp()
        code, out, _ = self.run_read(cdp)

        self.assertEqual(code, 0)
        self.assertEqual(out, "page text\n")
        self.assertEqual(cdp.calls[0], ("Target.createTarget",
                                        {"url": "https://www.seriouseats.com/x", "background": True}))
        self.assertEqual(cdp.calls[-1], ("Target.closeTarget", {"targetId": "T1"}))
        self.assertTrue(cdp.closed)

    def test_read_prints_non_string_values_as_json(self):
        code, out, _ = self.run_read(FakeCdp(value=["a", "ü"]))

        self.assertEqual(code, 0)
        self.assertEqual(out, '["a", "ü"]\n')

    def test_read_reports_page_exception_and_still_closes_tab(self):
        cdp = FakeCdp(exception="ReferenceError: nope is not defined")
        code, out, err = self.run_read(cdp)

        self.assertEqual(code, 1)
        self.assertIn("ReferenceError: nope is not defined", err)
        self.assertEqual(cdp.methods()[-1], "Target.closeTarget")

    def test_read_keep_leaves_tab_open_and_says_how_to_raise_it(self):
        cdp = FakeCdp()
        code, _, err = self.run_read(cdp, keep=True)

        self.assertEqual(code, 0)
        self.assertEqual(cdp.methods(), ["Target.createTarget", "Target.attachToTarget",
                                         "Runtime.evaluate", "Runtime.evaluate"])
        self.assertIn("`agent-chromium close T1`", err)


if __name__ == "__main__":
    unittest.main()
