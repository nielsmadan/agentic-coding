import importlib.machinery
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("tmx")
LOADER = importlib.machinery.SourceFileLoader("tmx", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
tmx = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(tmx)


class SessionNameTests(unittest.TestCase):
    def test_names_the_session_after_the_directory(self):
        self.assertEqual(tmx.session_name("/Users/me/wrksp/app", set()), "app")

    def test_replaces_characters_tmux_rejects(self):
        self.assertEqual(tmx.session_name("/Users/me/my.site:v2", set()), "my-site-v2")

    def test_numbers_a_name_that_is_taken(self):
        self.assertEqual(tmx.session_name("/x/app", {"app", "app-2"}), "app-3")


class ParseTests(unittest.TestCase):
    def test_parses_tmux_list_output(self):
        line = tmx.FIELD.join(["app", "1", "claude", "/Users/me/app"])
        self.assertEqual(
            tmx.parse_sessions(line + "\n"),
            [{"name": "app", "attached": True, "command": "claude", "path": "/Users/me/app"}],
        )

    def test_describe_marks_attached_and_shortens_home(self):
        session = {"name": "app", "attached": True, "command": "claude", "path": "/Users/me/app"}
        self.assertEqual(tmx.describe(session, "/Users/me"), "app *\tclaude\t~/app")


class ResumeTests(unittest.TestCase):
    def test_reads_the_directory_from_rl_dry_run(self):
        output = "dry run — nothing launched\n  directory: /Users/me/ac\n  argv: claude --resume abc\n"
        self.assertEqual(tmx.resume_directory(output), "/Users/me/ac")

    def test_dry_runs_only_when_rl_will_not_open_a_picker(self):
        self.assertTrue(tmx.knows_directory(["--last"]))
        self.assertTrue(tmx.knows_directory(["b072fd9b"]))
        self.assertFalse(tmx.knows_directory(["auth bug"]))

    def test_keeps_a_shell_open_after_the_command(self):
        self.assertEqual(
            tmx.shell_command(["rl", "resume", "--last"]),
            ["zsh", "-ic", "rl resume --last; exec zsh -i"],
        )


if __name__ == "__main__":
    unittest.main()
