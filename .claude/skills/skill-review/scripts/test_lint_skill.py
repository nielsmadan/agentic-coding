#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("lint_skill", Path(__file__).with_name("lint_skill.py"))
ls = importlib.util.module_from_spec(SPEC)
sys.modules["lint_skill"] = ls
SPEC.loader.exec_module(ls)

CLEANUP = ExitStack()
GOOD_DESCRIPTION = "Format tables in Markdown files. Use when the user asks to \"align this table\"."


def frontmatter(name: str = "demo", description: str = GOOD_DESCRIPTION) -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n"


class SkillFixture:
    def __init__(
        self,
        text: str,
        files: dict[str, str] | None = None,
        dirname: str = "demo",
        scope: str = "kit",
    ):
        self.path = Path(CLEANUP.enter_context(tempfile.TemporaryDirectory())) / dirname
        self.path.mkdir()
        (self.path / "SKILL.md").write_text(text)
        for rel, content in (files or {}).items():
            (self.path / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.path / rel).write_text(content)
        self.skill = ls.load_skill(scope, self.path)

    def lint(self, known: frozenset[str] = frozenset({"demo", "commit"})) -> list:
        return ls.lint(self.skill, known, frozenset(), "", frozenset())

    def checks(self, **kwargs) -> set[tuple[str, str]]:
        return {(f.severity, f.check) for f in self.lint(**kwargs)}


BODY = "\n# Demo\n\n## Instructions\n\nDo it.\n\n## Examples\n\nOne.\n\n## Troubleshooting\n\nNone.\n"


class FrontmatterTests(unittest.TestCase):
    def test_clean_skill_has_no_findings(self):
        self.assertEqual(SkillFixture(frontmatter() + BODY).lint(), [])

    def test_unquoted_colon_space_is_invalid_yaml(self):
        text = frontmatter(description="Review code. Deliberately narrow: no monads. Use when asked.") + BODY
        self.assertEqual(SkillFixture(text).checks(), {("error", "frontmatter")})

    def test_xml_tag_in_description_is_an_error(self):
        text = frontmatter(description='"Generate tests (--generate <target>). Use when asked."') + BODY
        self.assertIn(("error", "frontmatter"), SkillFixture(text).checks())

    def test_angle_brackets_in_argument_hint_are_allowed(self):
        text = "---\nname: demo\ndescription: " + GOOD_DESCRIPTION + "\nargument-hint: <topic>\n---\n" + BODY
        self.assertEqual(SkillFixture(text).lint(), [])

    def test_name_must_match_directory(self):
        findings = SkillFixture(frontmatter(name="other") + BODY).lint()
        self.assertEqual([(f.check, f.severity) for f in findings], [("name", "error")])

    def test_overlong_description_is_an_error(self):
        text = frontmatter(description="Use when asked. " + "x" * 1100) + BODY
        self.assertIn(("error", "description"), SkillFixture(text).checks())

    def test_first_person_description_warns(self):
        text = frontmatter(description="I can align tables. Use when asked.") + BODY
        self.assertEqual(SkillFixture(text).checks(), {("warn", "description")})

    def test_description_without_trigger_warns(self):
        text = frontmatter(description="Aligns Markdown tables.") + BODY
        self.assertEqual(SkillFixture(text).checks(), {("warn", "description")})

    def test_harness_override_description_is_checked(self):
        text = ("---\nname: demo\ndescription: " + GOOD_DESCRIPTION +
                "\nopencode:\n  description: Aligns tables.\n---\n" + BODY)
        messages = [f.message for f in SkillFixture(text).lint()]
        self.assertEqual(len(messages), 1)
        self.assertIn("opencode override", messages[0])


class BodyTests(unittest.TestCase):
    def test_harness_prefix_outside_fences_is_reported_once_with_lines(self):
        text = frontmatter() + BODY + "\nRun /commit then $commit.\n\n```\n/commit\n```\n"
        prefixed = [f for f in SkillFixture(text).lint() if f.check == "harness-prefix"]
        self.assertEqual(len(prefixed), 1)
        self.assertTrue(prefixed[0].message.endswith("(lines 20)"))

    def test_paths_are_not_mistaken_for_invocations(self):
        text = frontmatter() + BODY + "\nSee ~/.claude/skills/commit and src/commit.\n"
        self.assertEqual(SkillFixture(text).lint(), [])

    def test_missing_sections_are_info(self):
        text = frontmatter() + "\n# Demo\n\nDo it.\n"
        self.assertEqual(SkillFixture(text).checks(), {("info", "sections")})

    def test_dated_instruction_is_flagged(self):
        text = frontmatter() + BODY + "\nBefore March 2026, use the old API.\n"
        self.assertEqual(SkillFixture(text).checks(), {("info", "time-sensitive")})


class FileTests(unittest.TestCase):
    def test_reference_reached_through_another_reference_is_not_orphaned(self):
        text = frontmatter() + BODY + "\nRead [guide](references/guide.md).\n"
        files = {"references/guide.md": "Run `scripts/fix.py`.\n", "scripts/fix.py": "print(1)\n"}
        self.assertEqual(SkillFixture(text, files).lint(), [])

    def test_unmentioned_file_is_orphaned(self):
        fixture = SkillFixture(frontmatter() + BODY, {"references/unused.md": "x\n"})
        self.assertEqual(fixture.checks(), {("warn", "orphan")})

    def test_broken_link_warns(self):
        text = frontmatter() + BODY + "\nRead [guide](references/missing.md).\n"
        self.assertEqual(SkillFixture(text).checks(), {("warn", "links")})

    def test_reference_reachable_only_through_another_is_nested(self):
        text = frontmatter() + BODY + "\nRead [a](references/a.md).\n"
        files = {"references/a.md": "See [b](b.md).\n", "references/b.md": "Detail.\n"}
        self.assertEqual(SkillFixture(text, files).checks(), {("warn", "nesting")})

    def test_cross_link_to_a_reference_skill_md_names_is_fine(self):
        text = frontmatter() + BODY + "\nRead [a](references/a.md) and [b](references/b.md).\n"
        files = {"references/a.md": "See [b](b.md).\n", "references/b.md": "Detail.\n"}
        self.assertEqual(SkillFixture(text, files).lint(), [])

    def test_script_with_shebang_must_be_executable(self):
        text = frontmatter() + BODY + "\nRun `scripts/fix.py`.\n"
        fixture = SkillFixture(text, {"scripts/fix.py": "#!/usr/bin/env python3\n"})
        self.assertEqual(fixture.checks(), {("warn", "script-mode")})


class WiringTests(unittest.TestCase):
    def test_global_skill_must_be_classified_for_publishing(self):
        skill = SkillFixture(frontmatter() + BODY, scope="global").skill
        findings = ls.check_wiring(skill, frozenset(), "| `/demo` | Demo |", frozenset())
        self.assertEqual([(f.severity, f.check) for f in findings], [("error", "publish")])

    def test_repo_local_skill_needs_a_codex_link(self):
        skill = SkillFixture(frontmatter() + BODY, scope="repo-local").skill
        self.assertEqual([f.check for f in ls.check_wiring(skill, frozenset(), "", frozenset())], ["codex-link"])
        self.assertEqual(ls.check_wiring(skill, frozenset(), "", frozenset({"demo"})), [])


def tearDownModule() -> None:
    CLEANUP.close()


if __name__ == "__main__":
    unittest.main()
