import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETUP = r"""
source .airc.d/05-sandbox.zsh
source .airc.d/06-iterm-agent.zsh
source .airc.d/07-model-tiers.zsh
source .airc.d/claude.zsh
source .airc.d/codex.zsh
source .airc.d/pi.zsh
source .airc.d/cursor.zsh
_agent_raw_dir() { return 1; }
_agent_unsandboxed_profile() { return 1; }
_agent_sandboxed() { printf '%s\0' "$AGENT_HARNESS" "$@"; }
sops-exec() { printf '%s\0' "$AGENT_HARNESS" "$@"; }
"""


class ModelTiersTest(unittest.TestCase):
    def run_shell(self, *args, setup=""):
        result = subprocess.run(
            ["zsh", "-f", "-c", SETUP + setup + '\n"$@"', "test", *args],
            cwd=ROOT,
            capture_output=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        return result.stdout.decode().rstrip("\0").split("\0")

    def preset(self, provider, tier):
        return self.run_shell("_agent_model_tier", provider, tier)[0].strip().split(":")

    def test_each_tier_reaches_native_cli_with_matching_effort(self):
        prompt = "two words; $(echo unsafe) `echo unsafe`\nsecond line"
        for tier in ("low", "mid", "high", "xhigh", "max"):
            with self.subTest(tier=tier, command="claude"):
                model, effort = self.preset("anthropic", tier)
                self.assertEqual(
                    self.run_shell("claude", tier, "-p", prompt),
                    [
                        "claude",
                        "claude-local",
                        "claude",
                        "--model",
                        model,
                        "--effort",
                        effort,
                        "-p",
                        prompt,
                    ],
                )
            model, effort = self.preset("openai", tier)
            with self.subTest(tier=tier, command="codex"):
                self.assertEqual(
                    self.run_shell("codex", tier, "exec", prompt),
                    [
                        "codex",
                        "codex-local",
                        "codex",
                        "-c",
                        'sandbox_mode="danger-full-access"',
                        "-c",
                        'approval_policy="never"',
                        "--model",
                        model,
                        "-c",
                        f'model_reasoning_effort="{effort}"',
                        "exec",
                        prompt,
                    ],
                )
            with self.subTest(tier=tier, command="pix"):
                self.assertEqual(
                    self.run_shell("pix", tier, "-p", prompt),
                    [
                        "pi",
                        "pi-local",
                        "pi",
                        "--provider",
                        "openai",
                        "--model",
                        f"{model}:{effort}",
                        "-p",
                        prompt,
                    ],
                )

    def test_claude_and_codex_keep_explicit_options_and_literal_prompts(self):
        for command in ("claude", "codex"):
            for args in (
                (),
                ("--", "low"),
                ("--model", "custom", "high"),
                ("resume", "--last"),
                ("explain this",),
            ):
                with self.subTest(command=command, args=args):
                    self.assertEqual(
                        self.run_shell(
                            command, *args, setup="_agent_raw_dir() { return 0; }"
                        ),
                        [
                            command,
                            command,
                            *(
                                ["-s", "danger-full-access"]
                                if command == "codex"
                                else []
                            ),
                            *args,
                        ],
                    )

    def test_tier_survives_raw_routing_and_tracks_the_original_command(self):
        for command, provider in (("claude", "anthropic"), ("codex", "openai")):
            with self.subTest(command=command):
                model, effort = self.preset(provider, "mid")
                args = ["--model", model]
                args += (
                    ["--effort", effort]
                    if command == "claude"
                    else ["-c", f'model_reasoning_effort="{effort}"']
                )
                result = self.run_shell(
                    command,
                    "mid",
                    "hello",
                    setup=r"""
_agent_raw_dir() { return 0; }
_agent_iterm_run() {
  local recipe=$1 implementation=$2
  shift 2
  printf '%s\0' "$recipe"
  "$implementation" "$@"
}
""",
                )
                self.assertEqual(
                    result,
                    [
                        command,
                        command + "-raw",
                        command,
                        command,
                        *(
                            ["-s", "danger-full-access"]
                            if command == "codex"
                            else []
                        ),
                        *args,
                        "hello",
                    ],
                )

    def test_pix_without_tier_keeps_default_and_forwards_overrides(self):
        for args in ((), ("--", "low"), ("--model", "other:low", "--thinking", "high")):
            with self.subTest(args=args):
                self.assertEqual(
                    self.run_shell("pix", *args),
                    [
                        "pi",
                        "pi-local",
                        "pi",
                        "--provider",
                        "openai",
                        "--model",
                        "gpt-6.2-sol:max",
                        *args,
                    ],
                )

    def test_plain_pi_and_cursor_keep_their_own_argument_handling(self):
        self.assertEqual(
            self.run_shell("pi", "low", "hello"),
            ["pi", "pi-local", "pi", "low", "hello"],
        )
        self.assertEqual(
            self.run_shell("agent", "low", "hello"),
            ["cursor", "cursor-local", "cursor-agent", "low", "hello"],
        )
        self.assertEqual(
            self.run_shell("agent", "haiku", "hello"),
            [
                "cursor",
                "cursor-local",
                "cursor-agent",
                "--model",
                "claude-haiku-5-5-thinking-high",
                "hello",
            ],
        )

    def test_resourcing_preserves_presets(self):
        first = self.run_shell("codex", "high", "hello")
        self.assertEqual(self.run_shell("codex", "high", "hello", setup=SETUP), first)


if __name__ == "__main__":
    unittest.main()
