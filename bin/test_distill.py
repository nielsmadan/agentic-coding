from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).with_name("distill")
LOADER = importlib.machinery.SourceFileLoader("distill", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
distill = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(distill)


class FakeStdin:
    def __init__(self, data: str | bytes, tty: bool = False) -> None:
        self.buffer = io.BytesIO(data.encode() if isinstance(data, str) else data)
        self.tty = tty

    def isatty(self) -> bool:
        return self.tty


def run(argv: list[str], stdin: str | bytes = "", answer: str = "the answer"):
    out, err = io.StringIO(), io.StringIO()
    calls = []

    def fake_extract(fenced, ex, nonce):
        calls.append((fenced, ex))
        return answer

    with (
        mock.patch.object(sys, "argv", ["distill", *argv]),
        mock.patch.object(sys, "stdin", FakeStdin(stdin)),
        mock.patch.object(distill.exlib, "extract", fake_extract),
        redirect_stdout(out),
        redirect_stderr(err),
    ):
        code = distill.main()
    return code, out.getvalue(), err.getvalue(), calls


class DistillTests(unittest.TestCase):
    def test_stdin_is_fenced_as_one_document_and_answer_printed(self):
        code, out, _, calls = run(["what broke?"], stdin="the build broke on step 3")

        self.assertEqual(code, 0)
        self.assertEqual(out, "the answer\n")
        fenced, ex = calls[0]
        self.assertIn("DOCUMENT>>>\nthe build broke on step 3\n", fenced)
        self.assertEqual(ex.prompt, "what broke?")
        self.assertEqual(ex.model, distill.exlib.DEFAULT_MODEL)

    def test_invalid_utf8_on_stdin_is_replaced_not_fatal(self):
        code, out, _, calls = run(["what broke?"], stdin=b"build \xff broke")

        self.assertEqual(code, 0)
        self.assertEqual(out, "the answer\n")
        self.assertIn("build � broke", calls[0][0])

    def test_files_become_labelled_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp, "a.txt"), Path(tmp, "b.txt")
            a.write_text("alpha")
            b.write_text("beta")
            code, _, _, calls = run(["compare", str(a), str(b)])

        self.assertEqual(code, 0)
        fenced = calls[0][0]
        self.assertIn(f"SOURCE 1: {a}>>>\nalpha\n", fenced)
        self.assertIn(f"SOURCE 2: {b}>>>\nbeta\n", fenced)

    def test_empty_input_fails_without_calling_the_model(self):
        code, _, err, calls = run(["anything"], stdin="  \n")

        self.assertEqual(code, 1)
        self.assertIn("input is empty", err)
        self.assertEqual(calls, [])

    def test_oversized_input_fails_without_calling_the_model(self):
        with mock.patch.object(distill, "MAX_CHARS", 10):
            code, _, err, calls = run(["anything"], stdin="x" * 11)

        self.assertEqual(code, 1)
        self.assertIn("over the 10 limit", err)
        self.assertEqual(calls, [])

    def test_tty_stdin_without_files_is_rejected(self):
        with self.assertRaisesRegex(distill.exlib.ToolError, "no input"):
            distill.read_sources([], FakeStdin("", tty=True))

    def test_no_relevant_answer_warns(self):
        code, out, err, _ = run(
            ["deploy steps"],
            stdin="deploy notes",
            answer="NO_RELEVANT_CONTENT\nabout cats",
        )

        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("NO_RELEVANT_CONTENT"))
        self.assertIn("distill: warning: the input does not address the question", err)


if __name__ == "__main__":
    unittest.main()
