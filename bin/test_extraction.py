import io
import importlib.machinery
import importlib.util
import sys
from contextlib import redirect_stdout, redirect_stderr
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import extraction as ex


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.request = ex.Extraction("question", "candidate", 7)

    def test_request_preserves_text_usage_model_and_timeout(self):
        payload = {
            "choices": [{"message": {"content": " answer "}}],
            "model": "candidate",
            "usage": {"cost": 0.01},
        }
        with (
            mock.patch.object(ex, "require_key", return_value="test-token"),
            mock.patch.object(
                ex.OPENER, "open", return_value=io.StringIO(json.dumps(payload))
            ) as opened,
        ):
            result = ex.request_extract("source", self.request, "candidate", "nonce")
        self.assertEqual(result, payload)
        req = opened.call_args.args[0]
        body = json.loads(req.data)
        self.assertEqual(body["model"], "candidate")
        self.assertEqual(
            body["messages"], ex.build_messages("source", "question", "nonce")
        )
        self.assertEqual(body["temperature"], 0)
        self.assertEqual(opened.call_args.kwargs["timeout"], 7)

    def test_retryable_error_uses_fallback_once(self):
        with (
            mock.patch.object(
                ex,
                "post_extract",
                side_effect=[ex.ExtractError("busy", True), "fallback answer"],
            ) as call,
            mock.patch.object(ex, "warn"),
        ):
            self.assertEqual(
                ex.extract("source", self.request, "nonce"), "fallback answer"
            )
        self.assertEqual(
            [c.args[2] for c in call.call_args_list], ["candidate", ex.FALLBACK_MODEL]
        )

    def test_nonretryable_error_is_returned_without_fallback(self):
        with mock.patch.object(
            ex, "post_extract", side_effect=ex.ExtractError("bad request", False)
        ) as call:
            with self.assertRaisesRegex(ex.ExtractError, "bad request"):
                ex.extract("source", self.request, "nonce")
        self.assertEqual(call.call_count, 1)

    def test_both_failures_are_reported(self):
        with (
            mock.patch.object(
                ex,
                "post_extract",
                side_effect=[
                    ex.ExtractError("busy", True),
                    ex.ExtractError("down", True),
                ],
            ),
            mock.patch.object(ex, "warn"),
        ):
            with self.assertRaisesRegex(ex.ExtractError, "busy.*down"):
                ex.extract("source", self.request, "nonce")

    def test_malformed_payload_is_a_tool_error(self):
        for payload in [
            [],
            {},
            {"choices": None},
            {"choices": [{"message": {"content": None}}]},
        ]:
            with (
                self.subTest(payload=payload),
                mock.patch.object(ex, "require_key", return_value="test"),
                mock.patch.object(
                    ex.OPENER, "open", return_value=io.StringIO(json.dumps(payload))
                ),
            ):
                with self.assertRaises(ex.ExtractError):
                    ex.request_extract("source", self.request, "candidate", "nonce")

    def test_cross_host_redirect_strips_auth(self):
        req = ex.urllib.request.Request(
            "https://one.example/a", headers={"Authorization": "Bearer test"}
        )
        redirected = ex.NoAuthRedirect().redirect_request(
            req, None, 302, "", {}, "https://two.example/b"
        )
        self.assertEqual(redirected.full_url, "https://two.example/b")
        self.assertNotIn("Authorization", redirected.headers)

    def test_both_entrypoints_work_through_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ["distill", "jina-fetch"]:
                link = Path(directory, name)
                link.symlink_to(Path(__file__).resolve().with_name(name))
                result = subprocess.run(
                    [str(link), "--help"], capture_output=True, text=True, cwd=directory
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(ex.DEFAULT_MODEL, result.stdout)


class JinaCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        loader = importlib.machinery.SourceFileLoader(
            "jina_cli_test", str(Path(__file__).with_name("jina-fetch"))
        )
        spec = importlib.util.spec_from_loader(loader.name, loader)
        cls.cli = importlib.util.module_from_spec(spec)
        sys.modules[loader.name] = cls.cli
        loader.exec_module(cls.cli)

    def run_cli(self, args, pages):
        output = io.StringIO()
        with (
            mock.patch.object(sys, "argv", ["jina-fetch", *args]),
            mock.patch.object(self.cli, "_load_or_fail", side_effect=pages),
            mock.patch.object(self.cli, "report_page"),
            mock.patch.object(self.cli, "extract", return_value="extracted") as extract,
            redirect_stdout(output),
            redirect_stderr(io.StringIO()),
        ):
            result = self.cli.main()
        return result, output.getvalue(), extract

    def test_raw_returns_source_without_extraction(self):
        result, output, extract = self.run_cli(
            ["--raw", "https://example.com"], [ex.Page("url", "cache", "body")]
        )
        self.assertEqual((result, output), (0, "body\n"))
        extract.assert_not_called()

    def test_combined_labels_sources_and_preserves_explicit_model(self):
        result, output, extract = self.run_cli(
            [
                "--combined",
                "--model",
                "chosen",
                "https://a.example",
                "https://b.example",
                "compare",
            ],
            [ex.Page("a", "cache", "alpha"), ex.Page("b", "cache", "beta")],
        )
        self.assertEqual((result, output), (0, "extracted\n"))
        fenced, request, _ = extract.call_args.args
        self.assertIn("SOURCE 1: a", fenced)
        self.assertIn("SOURCE 2: b", fenced)
        self.assertEqual(request.model, "chosen")

    def test_partial_fetch_failure_keeps_nonzero_status_and_successful_answer(self):
        result, output, extract = self.run_cli(
            ["https://a.example", "https://b.example", "compare"],
            [ex.Page("a", "cache", "alpha"), self.cli.Failure("b", "failed")],
        )
        self.assertEqual((result, output), (1, "extracted\n"))
        self.assertEqual(extract.call_count, 1)


if __name__ == "__main__":
    unittest.main()
