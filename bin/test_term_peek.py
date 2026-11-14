import importlib.machinery
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("term-peek")
LOADER = importlib.machinery.SourceFileLoader("term_peek", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
term_peek = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(term_peek)


def pane(id, command, path="/repo"):
    return {"id": id, "command": command, "path": path}


class PickTests(unittest.TestCase):
    def test_picks_the_shell_beside_agent_panes(self):
        panes = [pane("me", "claude"), pane("a", "codex --yolo"), pane("t", "-zsh")]
        self.assertEqual(term_peek.pick(panes, "me", "/repo"), [pane("t", "-zsh")])

    def test_picks_a_lone_non_shell_pane_such_as_a_dev_server(self):
        panes = [pane("me", "claude"), pane("t", "npm run dev")]
        self.assertEqual(term_peek.pick(panes, "me", "/repo"), [pane("t", "npm run dev")])

    def test_prefers_the_shell_in_the_agents_directory(self):
        panes = [pane("me", "claude"), pane("x", "-zsh", "/elsewhere"), pane("t", "-zsh")]
        self.assertEqual(term_peek.pick(panes, "me", "/repo"), [pane("t", "-zsh")])

    def test_returns_every_candidate_when_ambiguous(self):
        panes = [pane("me", "claude"), pane("t", "-zsh"), pane("u", "bash")]
        self.assertEqual(
            term_peek.pick(panes, "me", "/repo"), [pane("t", "-zsh"), pane("u", "bash")]
        )

    def test_agent_under_nono_counts_as_an_agent(self):
        panes = [pane("me", "claude"), pane("a", "nono run -p pi-local -- pi"), pane("t", "zsh")]
        self.assertEqual(term_peek.pick(panes, "me", "/repo"), [pane("t", "zsh")])


class ParseAndTailTests(unittest.TestCase):
    def test_parses_osascript_records(self):
        raw = "A\x1f/repo\x1f-zsh\x1eB\x1f/repo\x1fclaude\x1e\n"
        self.assertEqual(
            term_peek.parse_panes(raw), [pane("A", "-zsh"), pane("B", "claude")]
        )

    def test_tail_drops_trailing_blank_screen_rows(self):
        self.assertEqual(term_peek.tail("one\ntwo\nthree\n\n\n\n", 2), "two\nthree")

    def test_tail_zero_returns_everything(self):
        self.assertEqual(term_peek.tail("one\ntwo\n", 0), "one\ntwo")


if __name__ == "__main__":
    unittest.main()
