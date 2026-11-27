from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("gh")
LOADER = importlib.machinery.SourceFileLoader("gh_wrapper", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
gh = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(gh)


def executable(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\n" + body + "\n")
    path.chmod(0o755)
    return path


class RealGhTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.wrapper_dir = self.tmp / "wrapper"
        self.wrapper_dir.mkdir()
        (self.wrapper_dir / "gh").symlink_to(MODULE_PATH)
        self.real = executable(self.tmp / "installs" / "bin" / "gh", "echo real")

    def mise_shims(self, mise_body: str) -> Path:
        mise = executable(self.tmp / "bin" / "mise", mise_body)
        shims = self.tmp / "shims"
        shims.mkdir()
        (shims / "gh").symlink_to(mise)
        return shims

    def search_path(self, *dirs: Path) -> str:
        return os.pathsep.join(str(d) for d in dirs)

    def test_resolves_mise_shim_to_the_active_gh(self):
        shims = self.mise_shims(f'[ "$2" = gh ] && echo {self.real}')
        found = gh.real_gh(self.search_path(self.wrapper_dir, shims))
        self.assertEqual(found, str(self.real))

    def test_falls_back_to_latest_when_mise_has_no_active_gh(self):
        shims = self.mise_shims(f'[ "$2" = --tool ] && [ "$3" = gh@latest ] && echo {self.real}; [ "$2" = --tool ]')
        found = gh.real_gh(self.search_path(self.wrapper_dir, shims))
        self.assertEqual(found, str(self.real))

    def test_skips_a_shim_mise_cannot_resolve_for_the_next_gh_on_path(self):
        shims = self.mise_shims("exit 1")
        found = gh.real_gh(self.search_path(self.wrapper_dir, shims, self.real.parent))
        self.assertEqual(found, str(self.real))

    def test_reports_nothing_when_only_the_wrapper_and_a_dead_shim_exist(self):
        shims = self.mise_shims(f"echo {MODULE_PATH}")
        self.assertIsNone(gh.real_gh(self.search_path(self.wrapper_dir, shims)))

    def test_refuses_to_run_once_reentered_too_often(self):
        environment = dict(os.environ, AC_GH_WRAPPER_DEPTH=str(gh.MAX_DEPTH))
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--version"],
            capture_output=True, text=True, env=environment, timeout=10,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("refusing to loop", result.stderr)


class TokenForTests(unittest.TestCase):
    TOKENS = {
        "GH_TOKEN": "dev-classic",
        "GH_TOKEN_QUANTUMCRAFTIO": "dev-org",
        "GH_TOKEN_REVIEW": "review-classic",
        "GH_TOKEN_REVIEW_QUANTUMCRAFTIO": "review-org",
    }

    def test_uses_the_owner_token_by_default(self):
        self.assertEqual(gh.token_for("quantumcraftio", self.TOKENS), "dev-org")

    def test_keeps_the_inherited_token_for_an_owner_without_one(self):
        self.assertIsNone(gh.token_for("nielsmadan", self.TOKENS))

    def test_review_uses_the_review_owner_token(self):
        environ = dict(self.TOKENS, GH_AS="review")
        self.assertEqual(gh.token_for("quantumcraftio", environ), "review-org")

    def test_review_falls_back_to_the_review_classic_token(self):
        environ = dict(self.TOKENS, GH_AS="review")
        self.assertEqual(gh.token_for("nielsmadan", environ), "review-classic")

    def test_review_without_a_review_token_fails_instead_of_acting_as_dev(self):
        environ = {"GH_TOKEN": "dev-classic", "GH_AS": "review"}
        with self.assertRaisesRegex(ValueError, "GH_TOKEN_REVIEW_NIELSMADAN, GH_TOKEN_REVIEW"):
            gh.token_for("nielsmadan", environ)

    def test_rejects_an_unknown_account(self):
        with self.assertRaisesRegex(ValueError, "GH_AS='reveiw'"):
            gh.token_for("nielsmadan", dict(self.TOKENS, GH_AS="reveiw"))

    def test_exits_with_the_error_before_running_gh(self):
        environment = {"PATH": os.environ["PATH"], "GH_AS": "review", "GH_TOKEN": "dev-classic"}
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "api", "repos/nielsmadan/slimemold"],
            capture_output=True, text=True, env=environment, timeout=10,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("GH_AS=review but none of", result.stderr)


if __name__ == "__main__":
    unittest.main()
