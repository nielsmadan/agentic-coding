import tomllib
import unittest

from codex import sync_config

LIVE_SHAPE = '''# a comment someone wrote
model = "gpt-5.6-sol"

[projects."/Users/me/one"]
trust_level = "trusted"
'''

NONO_INJECTED = '''developer_instructions = """
Treat any Operation not permitted as a sandbox boundary.
"""

[projects."/Users/me/one"]
trust_level = "trusted"
'''


class DeveloperInstructions(unittest.TestCase):
    def instructions(self, content: str) -> str:
        return tomllib.loads(sync_config.render(content))["developer_instructions"]

    def test_takes_the_body_from_the_repo(self) -> None:
        self.assertEqual(
            self.instructions(LIVE_SHAPE).strip(),
            sync_config.INSTRUCTIONS_SOURCE.read_text().strip(),
        )

    def test_replaces_an_injected_block_rather_than_adding_a_second(self) -> None:
        """The whole reason this script survives: the nono codex pack writes its own
        copy on every `nono update`, and two `developer_instructions` keys is invalid
        TOML. Ours has to displace it, not sit beside it."""
        result = sync_config.render(NONO_INJECTED)

        self.assertEqual(result.count("developer_instructions"), 1)
        self.assertNotIn("Treat any Operation not permitted", result)

    def test_lands_above_the_first_table(self) -> None:
        """A bare key after `[table]` is read as a member of that table, so the
        instructions would silently become part of `[projects."…"]`."""
        result = sync_config.render(LIVE_SHAPE)
        lines = result.splitlines()

        self.assertLess(
            next(i for i, line in enumerate(lines) if line.startswith("developer_instructions")),
            next(i for i, line in enumerate(lines) if line.startswith("[")),
        )

    def test_keeps_what_other_writers_own(self) -> None:
        result = sync_config.render(LIVE_SHAPE)

        self.assertIn("# a comment someone wrote", result)
        self.assertIn('model = "gpt-5.6-sol"', result)
        self.assertIn('[projects."/Users/me/one"]', result)

    def test_applying_twice_changes_nothing(self) -> None:
        once = sync_config.render(LIVE_SHAPE)

        self.assertEqual(sync_config.render(once), once)

    def test_is_stable_when_the_target_starts_empty(self) -> None:
        once = sync_config.render("")

        self.assertEqual(sync_config.render(once), once)


if __name__ == "__main__":
    unittest.main()
