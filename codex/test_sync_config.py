import tempfile
import tomllib
import unittest
from pathlib import Path

from codex import sync_config


LIVE_SHAPE = '''# Codex CLI configuration

approval_policy = "on-request"
personality = "pragmatic"
model = "gpt-0.1-old"
model_reasoning_effort = "low"

# >>> nono:nolabs-ai-codex >>>

developer_instructions = """
A denial footer is not a failure.
model = "this is prose inside a multiline string"
"""

# <<< nono:nolabs-ai-codex <<<

[projects."/Users/someone/wrksp/thing"]
trust_level = "trusted"

[mcp_servers.context7]
command = "npx"
'''


def defaults() -> dict:
    return tomllib.loads(sync_config.MODEL_DEFAULTS_SOURCE.read_text())


class ModelDefaultsTests(unittest.TestCase):
    def render(self, current: str) -> str:
        return sync_config.render(current, sync_config.load_managed_source())

    def assert_stable(self, current: str) -> str:
        once = self.render(current)
        self.assertEqual(once, self.render(once))
        return once

    def test_replaces_the_named_keys_in_place(self) -> None:
        result = self.assert_stable(LIVE_SHAPE)
        parsed = tomllib.loads(result)

        for key, value in defaults().items():
            self.assertEqual(parsed[key], value)

    def test_keeps_what_other_writers_own(self) -> None:
        result = self.assert_stable(LIVE_SHAPE)
        parsed = tomllib.loads(result)

        self.assertEqual(parsed["approval_policy"], "on-request")
        self.assertEqual(parsed["personality"], "pragmatic")
        self.assertIn("/Users/someone/wrksp/thing", parsed["projects"])
        self.assertIn("# >>> nono:nolabs-ai-codex >>>", result)
        self.assertIn("# Codex CLI configuration", result)

    def test_adds_keys_the_target_lacks_above_the_first_table(self) -> None:
        without = "\n".join(
            line
            for line in LIVE_SHAPE.splitlines()
            if not line.startswith(("model =", "model_reasoning_effort ="))
        )
        result = self.assert_stable(without)
        parsed = tomllib.loads(result)

        for key, value in defaults().items():
            self.assertEqual(parsed[key], value)

    def test_lands_the_added_keys_beside_the_other_scalars(self) -> None:
        without = "\n".join(
            line
            for line in LIVE_SHAPE.splitlines()
            if not line.startswith(("model =", "model_reasoning_effort ="))
        )
        lines = self.assert_stable(without).splitlines()

        self.assertLess(
            lines.index('model = "%s"' % defaults()["model"]),
            lines.index("# >>> nono:nolabs-ai-codex >>>"),
        )

    def test_takes_developer_instructions_from_the_repo(self) -> None:
        # The whole value is replaced, so the fixture's body — including the
        # `model =` line inside it — is gone rather than preserved. That line is
        # in the fixture to prove it never reaches the top level: the key surgery
        # runs after the block is stripped, so it cannot rewrite prose.
        parsed = tomllib.loads(self.assert_stable(LIVE_SHAPE))

        self.assertNotIn("prose inside a multiline string", parsed["developer_instructions"])
        self.assertEqual(
            parsed["developer_instructions"].strip(),
            sync_config.INSTRUCTIONS_SOURCE.read_text().strip(),
        )
        self.assertEqual(parsed["model"], defaults()["model"])

    def test_is_stable_when_the_target_starts_empty(self) -> None:
        # A populated target reuses what is on disk and hides this: an empty one
        # rendered a blank line and the managed comment in a different place on
        # each run, so a re-render diff would report drift the renderer created.
        self.assert_stable("")

    def test_rejects_a_source_holding_a_nested_table(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "model-defaults.toml"
            source.write_text('model = "x"\n\n[nested]\nkey = "y"\n')
            original = sync_config.MODEL_DEFAULTS_SOURCE
            sync_config.MODEL_DEFAULTS_SOURCE = source
            try:
                # Matched by message: without the guard a nested table still
                # raises ValueError further down, out of toml_value, so a bare
                # assertRaises passes whether the guard is there or not.
                with self.assertRaisesRegex(ValueError, "may only hold top-level keys"):
                    sync_config.set_model_defaults(LIVE_SHAPE)
            finally:
                sync_config.MODEL_DEFAULTS_SOURCE = original


if __name__ == "__main__":
    unittest.main()
