import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

WRAPPER = Path(__file__).with_name("cf-as")


class CloudflareAccountTests(unittest.TestCase):
    def run_wrapper(self, args, overrides=None, cwd=None):
        environment = {
            "PATH": os.defpath,
            "CLOUDFLARE_API_TOKEN_PERSONAL": "fake-personal-token",
            "CLOUDFLARE_API_TOKEN_QUANTUMCRAFT": "fake-qc-token",
            **(overrides or {}),
        }
        return subprocess.run(
            [sys.executable, str(WRAPPER), *args],
            env=environment,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

    def test_selects_credentials_and_preserves_arguments_and_working_directory(self):
        probe = (
            "import json, os, sys; "
            "print(json.dumps([os.environ['CLOUDFLARE_API_TOKEN'], "
            "os.environ['CLOUDFLARE_ACCOUNT_ID'], os.getcwd(), sys.argv[1:]]))"
        )
        for account, token, account_id in (
            ("personal", "fake-personal-token", "7cd3590a7fcf960fcf9cf1543ad17dd3"),
            ("qc", "fake-qc-token", "c350638ab95bb03d85b470cfa83a57cd"),
        ):
            with self.subTest(account=account), tempfile.TemporaryDirectory() as cwd:
                result = self.run_wrapper(
                    [
                        account,
                        sys.executable,
                        "-c",
                        probe,
                        "two words",
                        "$(literal)",
                        "",
                    ],
                    {"CLOUDFLARE_API_TOKEN": "stale", "CLOUDFLARE_ACCOUNT_ID": "stale"},
                    cwd=cwd,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    json.loads(result.stdout),
                    [
                        token,
                        account_id,
                        str(Path(cwd).resolve()),
                        ["two words", "$(literal)", ""],
                    ],
                )

    def test_removes_alternate_credentials_and_preserves_unrelated_environment(self):
        alternates = {
            "CLOUDFLARE_API_KEY": "fake-key",
            "CLOUDFLARE_EMAIL": "other@example.com",
            "CF_API_KEY": "fake-key",
            "CF_EMAIL": "other@example.com",
            "CF_API_TOKEN": "fake-other-token",
            "CF_ACCOUNT_ID": "other-account",
        }
        probe = (
            "import json, os; "
            f"print(json.dumps({{k: os.environ.get(k) for k in {[*alternates, 'MARKER']!r}}}))"
        )
        result = self.run_wrapper(
            ["personal", sys.executable, "-c", probe], {**alternates, "MARKER": "kept"}
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout), {**dict.fromkeys(alternates), "MARKER": "kept"}
        )

    def test_missing_selected_token_does_not_launch_the_command_or_fall_back(self):
        for account, variable in (
            ("personal", "CLOUDFLARE_API_TOKEN_PERSONAL"),
            ("qc", "CLOUDFLARE_API_TOKEN_QUANTUMCRAFT"),
        ):
            with self.subTest(account=account), tempfile.TemporaryDirectory() as cwd:
                marker = Path(cwd) / "launched"
                result = self.run_wrapper(
                    [
                        account,
                        sys.executable,
                        "-c",
                        "from pathlib import Path; Path('launched').touch()",
                    ],
                    {variable: "", "CLOUDFLARE_API_TOKEN": "fake-fallback-token"},
                    cwd=cwd,
                )
                self.assertEqual(result.returncode, 78)
                self.assertIn(f"{variable} is missing or empty", result.stderr)
                self.assertFalse(marker.exists())

    def test_rejects_unknown_accounts_and_missing_commands(self):
        for args in (["unknown", "echo", "hello"], ["personal"]):
            with self.subTest(args=args):
                result = self.run_wrapper(args)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: cf-as", result.stderr)

    def test_preserves_child_exit_status(self):
        result = self.run_wrapper(["qc", sys.executable, "-c", "raise SystemExit(23)"])
        self.assertEqual(result.returncode, 23)

    def test_reports_missing_executable(self):
        result = self.run_wrapper(["personal", "/no-such-cf-as-test-command"])
        self.assertEqual(result.returncode, 127)
        self.assertIn("command not found", result.stderr)


if __name__ == "__main__":
    unittest.main()
