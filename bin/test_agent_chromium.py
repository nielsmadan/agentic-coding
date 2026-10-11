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


if __name__ == "__main__":
    unittest.main()
