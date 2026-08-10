from __future__ import annotations

import importlib.util
import json
import tempfile
import tomllib
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("sync.py")
SPEC = importlib.util.spec_from_file_location("mcp_sync", MODULE_PATH)
sync = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(sync)


SERVERS = {
    "context7": {
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@upstash/context7-mcp"],
    },
    "jina": {
        "transport": "http",
        "url": "https://mcp.jina.ai/v1",
        "auth_env_var": "JINA_API_KEY",
    },
}


class McpSyncTests(unittest.TestCase):
    def test_opencode_local_merges_command_and_args(self):
        rendered = next(iter(sync.render_opencode(SERVERS).values()))
        mcp = json.loads(rendered)["mcp"]

        self.assertEqual(
            mcp["context7"],
            {"type": "local", "command": ["npx", "-y", "@upstash/context7-mcp"]},
        )
        self.assertEqual(
            mcp["jina"]["headers"]["Authorization"],
            "Bearer {env:JINA_API_KEY}",
        )

    def test_opencode_preserves_permission_key(self):
        rendered = next(iter(sync.render_opencode(SERVERS).values()))
        config = json.loads(rendered)

        self.assertIn("permission", config)
        self.assertIn("$schema", config)

    def test_auth_is_an_env_var_reference_never_a_token(self):
        rendered = {
            path.name: content
            for path, content in {
                **sync.render_claude(SERVERS),
                **sync.render_codex(SERVERS),
                **sync.render_opencode(SERVERS),
            }.items()
        }

        self.assertIn('bearer_token_env_var = "JINA_API_KEY"', rendered["config.toml"])
        self.assertIn(
            "Bearer ${JINA_API_KEY}",
            json.loads(rendered["mcp-servers.generated.json"])["jina"]["headers"][
                "Authorization"
            ],
        )
        for name, content in rendered.items():
            self.assertNotIn("Bearer sk-", content, name)

    def test_codex_output_is_valid_toml(self):
        rendered = next(iter(sync.render_codex(SERVERS).values()))
        parsed = tomllib.loads(rendered)

        self.assertEqual(
            parsed["mcp_servers"]["context7"]["args"], ["-y", "@upstash/context7-mcp"]
        )
        self.assertEqual(parsed["mcp_servers"]["jina"]["url"], "https://mcp.jina.ai/v1")

    def test_source_file_parses(self):
        servers = sync.parse_source()

        self.assertIn("jina", servers)
        self.assertEqual(sorted(servers), list(servers))

    def test_transport_is_validated(self):
        bad = {
            "unknown transport": '[a]\ntransport = "carrier-pigeon"\n',
            "http without url": '[a]\ntransport = "http"\n',
            "stdio without command": '[a]\ntransport = "stdio"\n',
        }
        original = sync.SOURCE
        with tempfile.TemporaryDirectory() as tmp:
            probe = Path(tmp) / "servers.toml"
            sync.SOURCE = probe
            try:
                for label, content in bad.items():
                    with self.subTest(label):
                        probe.write_text(content)
                        with self.assertRaises(ValueError):
                            sync.parse_source()
            finally:
                sync.SOURCE = original


if __name__ == "__main__":
    unittest.main()
