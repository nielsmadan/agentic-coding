import tomllib
import unittest

from codex.strip_nono_block import strip_nono_block


class StripNonoBlockTests(unittest.TestCase):
    def test_removes_instructions_absorbed_into_the_last_table(self) -> None:
        config = (
            'model = "gpt-6-astra"\n'
            "\n"
            "[tui.keymap.chat]\n"
            'edit_queued_message = "alt-o"\n'
            "\n"
            "# >>> nono:nolabs-ai-codex >>>\n"
            'developer_instructions = """\n'
            "Offer `nono run --allow`.\n"
            '"""\n'
            "# <<< nono:nolabs-ai-codex <<<\n"
        )

        stripped = strip_nono_block(config)

        self.assertEqual(
            tomllib.loads(stripped),
            {"model": "gpt-6-astra", "tui": {"keymap": {"chat": {"edit_queued_message": "alt-o"}}}},
        )

    def test_keeps_settings_codex_wrote_between_the_markers(self) -> None:
        config = (
            "# >>> nono:nolabs-ai-codex >>>\n"
            'service_tier = "default"\n'
            "\n"
            '[plugins."chrome@openai-bundled"]\n'
            "enabled = true\n"
            "# <<< nono:nolabs-ai-codex <<<\n"
        )

        stripped = strip_nono_block(config)

        self.assertEqual(
            stripped,
            'service_tier = "default"\n\n[plugins."chrome@openai-bundled"]\nenabled = true\n',
        )

    def test_keeps_developer_instructions_outside_the_block(self) -> None:
        mine = 'developer_instructions = """\nmine\n"""\n'
        config = "# >>> nono:nolabs-ai-codex >>>\n# <<< nono:nolabs-ai-codex <<<\n" + mine

        self.assertEqual(strip_nono_block(config), mine)


if __name__ == "__main__":
    unittest.main()
