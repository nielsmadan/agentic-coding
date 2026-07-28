from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("sync.py")
SPEC = importlib.util.spec_from_file_location("permission_sync", MODULE_PATH)
sync = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(sync)


class PermissionSyncTests(unittest.TestCase):
    def test_pi_mcp_rules_use_native_permission_targets(self):
        rules = {
            "allow": [],
            "ask": [],
            "deny": [],
            "mcp_allow": ["jina/*"],
            "mcp_ask": [],
            "mcp_deny": ["danger/delete"],
        }

        rendered = next(iter(sync.render_pi(rules).values()))
        mcp = json.loads(rendered)["permission"]["mcp"]

        self.assertEqual(mcp["jina_*"], "allow")
        self.assertEqual(mcp["mcp_server_jina"], "allow")
        self.assertEqual(mcp["mcp_connect_jina"], "allow")
        self.assertEqual(mcp["danger_delete"], "deny")
        self.assertNotIn("jina/*", mcp)
        self.assertNotIn("danger/delete", mcp)


if __name__ == "__main__":
    unittest.main()
