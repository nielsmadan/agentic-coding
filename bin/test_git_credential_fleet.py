from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent
ROOT = BIN.parent
MODULE_PATH = BIN / "git-credential-fleet"
LOADER = importlib.machinery.SourceFileLoader("git_credential_fleet", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
helper = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(helper)

TOKENS = {"GH_TOKEN": "public-token", "GH_TOKEN_QUANTUMCRAFTIO": "org-token"}


def request(path: str, host: str = "github.com") -> str:
    return f"protocol=https\nhost={host}\npath={path}\n"


class AnswerTests(unittest.TestCase):
    def test_org_repo_gets_the_org_token(self):
        out = helper.answer("get", request("quantumcraftio/agents.git"), TOKENS)
        self.assertEqual(out, "username=x-access-token\npassword=org-token\n")

    def test_owner_without_its_own_token_gets_gh_token(self):
        for path in ("nielsmadan/loadout.git", "quantumcraftdev/rc.git"):
            with self.subTest(path=path):
                out = helper.answer("get", request(path), TOKENS)
                self.assertEqual(out, "username=x-access-token\npassword=public-token\n")

    def test_request_without_a_path_gets_gh_token(self):
        out = helper.answer("get", "protocol=https\nhost=github.com\n", TOKENS)
        self.assertEqual(out, "username=x-access-token\npassword=public-token\n")

    def test_other_hosts_get_no_answer(self):
        self.assertEqual(helper.answer("get", request("a/b.git", host="gitlab.com"), TOKENS), "")

    def test_store_and_erase_are_ignored(self):
        for action in ("store", "erase"):
            with self.subTest(action=action):
                self.assertEqual(helper.answer(action, request("quantumcraftio/agents.git"), TOKENS), "")


class FleetGitconfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.spy_log = self.tmp / "keychain-called"
        spy = self.tmp / "spybin" / "git-credential-osxkeychain"
        spy.parent.mkdir()
        spy.write_text(f"#!/bin/sh\ntouch {shlex.quote(str(self.spy_log))}\n")
        spy.chmod(0o755)
        system = self.tmp / "system-gitconfig"
        system.write_text(f"[credential]\n\thelper = {spy}\n")
        self.env = {
            "HOME": str(self.tmp),
            "PATH": os.pathsep.join([str(BIN), os.environ["PATH"]]),
            "GIT_CONFIG_GLOBAL": str(ROOT / "fleet" / "gitconfig"),
            "GIT_CONFIG_SYSTEM": str(system),
            "GIT_TERMINAL_PROMPT": "0",
            **TOKENS,
        }

    def run_git(self, *args: str, stdin: str = "", cwd: Path | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args], input=stdin, env=self.env, cwd=cwd or self.tmp,
            capture_output=True, text=True,
        )

    def git(self, *args: str, stdin: str = "", cwd: Path | None = None) -> str:
        result = self.run_git(*args, stdin=stdin, cwd=cwd)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def repo(self) -> Path:
        repo = self.tmp / "repo"
        self.git("init", "-q", str(repo))
        return repo

    def test_fill_answers_from_the_fleet_helper_instead_of_the_keychain(self):
        out = self.git("credential", "fill", stdin="url=https://github.com/quantumcraftio/agents.git\n\n")
        self.assertIn("password=org-token\n", out)
        self.assertFalse(self.spy_log.exists(), "the system osxkeychain helper ran")

    def test_ssh_remotes_are_fetched_over_https(self):
        out = self.git("ls-remote", "--get-url", "git@github.com:nielsmadan/loadout.git")
        self.assertEqual(out.strip(), "https://github.com/nielsmadan/loadout.git")

    def test_commits_are_signed_with_the_fleet_key(self):
        keys = self.tmp / "fleet" / "keys"
        keys.mkdir(parents=True)
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(keys / "signing")], check=True)
        repo = self.repo()
        self.git("commit", "-q", "--allow-empty", "-m", "x", cwd=repo)
        self.assertIn("-----BEGIN SSH SIGNATURE-----", self.git("cat-file", "commit", "HEAD", cwd=repo))

    def test_commit_fails_without_the_fleet_key(self):
        result = self.run_git("commit", "-q", "--allow-empty", "-m", "x", cwd=self.repo())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fleet/keys/signing", result.stderr)

    def test_commits_carry_the_dev_accounts_noreply_identity(self):
        self.assertEqual(self.git("config", "user.email").strip(),
                         "354587309+quantumcraftdev@users.noreply.github.com")


class FleetSyncEnvTests(unittest.TestCase):
    def test_env_points_git_at_the_fleet_gitconfig(self):
        out = subprocess.run([str(BIN / "fleet-sync"), "--env"], capture_output=True, text=True, check=True).stdout
        self.assertIn(f"export GIT_CONFIG_GLOBAL={ROOT / 'fleet' / 'gitconfig'}\n", out)


if __name__ == "__main__":
    unittest.main()
