import contextlib
import io
import os
import tempfile
import unittest
import unittest.mock
from dataclasses import dataclass
from pathlib import Path

from publish import sync


@dataclass(frozen=True)
class FakeSkill:
    """Test double matching the shape render_tree needs from loadout's Skill."""

    name: str
    document: Path
    supporting: tuple[Path, ...]


class ManifestTest(unittest.TestCase):
    def test_load_manifest_derives_publish_from_groups(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "skills.toml"
            path.write_text(
                'private = ["c"]\n[groups]\nCore = ["a", "b"]\nExtra = ["d"]\n',
                encoding="utf-8",
            )
            publish, private, groups = sync.load_manifest(path)
            self.assertEqual(publish, ["a", "b", "d"])
            self.assertEqual(private, ["c"])
            self.assertEqual(groups, [("Core", ["a", "b"]), ("Extra", ["d"])])

    def test_available_skills_lists_only_directories_with_skill_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "real").mkdir()
            (root / "real" / "SKILL.md").write_text("x", encoding="utf-8")
            (root / "empty").mkdir()
            (root / "README.md").write_text("x", encoding="utf-8")
            self.assertEqual(sync.available_skills(root), ["real"])

    def test_unclassified_skill_is_an_error(self):
        errors = sync.manifest_errors(["a", "b"], ["a"], [])
        self.assertEqual(len(errors), 1)
        self.assertIn("b", errors[0])
        self.assertIn("unclassified", errors[0])

    def test_skill_in_both_lists_is_an_error(self):
        errors = sync.manifest_errors(["a"], ["a"], ["a"])
        self.assertTrue(any("both" in e for e in errors))

    def test_manifest_entry_without_a_skill_is_an_error(self):
        errors = sync.manifest_errors(["a"], ["a", "ghost"], [])
        self.assertTrue(any("no such skill" in e for e in errors))

    def test_fully_classified_manifest_has_no_errors(self):
        self.assertEqual(sync.manifest_errors(["a", "b"], ["a"], ["b"]), [])

    def test_duplicate_publish_entry_is_an_error(self):
        errors = sync.manifest_errors(["a", "b"], ["a", "a"], ["b"])
        self.assertTrue(
            any("a" in e and "more than once" in e and "publish" in e for e in errors)
        )

    def test_duplicate_private_entry_is_an_error(self):
        errors = sync.manifest_errors(["a", "b"], ["a"], ["b", "b"])
        self.assertTrue(
            any("b" in e and "more than once" in e and "private" in e for e in errors)
        )


class GuardTest(unittest.TestCase):
    def test_parse_frontmatter_reads_keys(self):
        text = "---\nname: demo\ndescription: A demo skill.\n---\n\nbody\n"
        self.assertEqual(
            sync.parse_frontmatter(text),
            {"name": "demo", "description": "A demo skill."},
        )

    def test_parse_frontmatter_returns_empty_without_frontmatter(self):
        self.assertEqual(sync.parse_frontmatter("# no frontmatter\n"), {})

    def test_reference_pattern_matches_backticked_name(self):
        pattern = sync.reference_pattern("aiconf")
        self.assertTrue(pattern.search("Claude Code and `aiconf` put project skills"))

    def test_reference_pattern_matches_slash_command(self):
        pattern = sync.reference_pattern("permission")
        self.assertTrue(pattern.search("Use /permission to change permissions."))

    def test_reference_pattern_ignores_path_like_prose(self):
        pattern = sync.reference_pattern("permission")
        self.assertIsNone(pattern.search("Setup/permission/config friction"))

    def test_reference_pattern_ignores_the_bare_word(self):
        pattern = sync.reference_pattern("permission")
        self.assertIsNone(pattern.search("the permission model is fine"))

    def test_personal_path_is_an_error(self):
        text = "---\nname: demo\ndescription: d\n---\nSee ~/ac/nono for details.\n"
        errors = sync.guard_errors("demo", text, [])
        self.assertTrue(any("personal string" in e for e in errors))

    def test_name_must_match_directory(self):
        text = "---\nname: other\ndescription: d\n---\nbody\n"
        errors = sync.guard_errors("demo", text, [])
        self.assertTrue(any("does not match" in e for e in errors))

    def test_description_over_1024_chars_is_an_error(self):
        text = "---\nname: demo\ndescription: " + ("x" * 1025) + "\n---\nbody\n"
        errors = sync.guard_errors("demo", text, [])
        self.assertTrue(any("description" in e for e in errors))

    def test_description_with_pipe_is_an_error(self):
        text = "---\nname: demo\ndescription: grep | head examples\n---\nbody\n"
        errors = sync.guard_errors("demo", text, [])
        self.assertTrue(any("README table" in e for e in errors))

    def test_reference_to_private_skill_is_an_error(self):
        text = "---\nname: demo\ndescription: d\n---\nRun `aiconf` first.\n"
        errors = sync.guard_errors("demo", text, ["aiconf"])
        self.assertTrue(any("aiconf" in e for e in errors))

    def test_private_reference_reports_line_and_every_occurrence(self):
        text = (
            "---\nname: demo\ndescription: d\n---\n"
            "Run `aiconf` first.\nThen `aiconf` again.\n"
        )
        errors = sync.guard_errors("demo", text, ["aiconf"])
        hits = [e for e in errors if "references unpublished skill 'aiconf'" in e]
        self.assertEqual(len(hits), 2)
        self.assertIn("(SKILL.md:5)", hits[0])
        self.assertIn("(SKILL.md:6)", hits[1])

    def test_home_variable_personal_path_is_an_error(self):
        text = "---\nname: demo\ndescription: d\n---\nRun $HOME/rc/bin/tool now.\n"
        errors = sync.guard_errors("demo", text, [])
        self.assertTrue(any("personal string" in e for e in errors))

    def test_clean_skill_has_no_errors(self):
        text = "---\nname: demo\ndescription: A clean skill.\n---\nbody\n"
        self.assertEqual(sync.guard_errors("demo", text, ["aiconf"]), [])

    def test_generic_users_path_in_an_example_is_not_an_error(self):
        # doc/references/principles.md legitimately shows /Users/name/... as a
        # path NOT to write. Only the real identity is a leak.
        text = (
            "---\nname: demo\ndescription: d\n---\n"
            "Bad: `/Users/name/projects/app`. Check for `/Users/` in docs.\n"
        )
        self.assertEqual(sync.guard_errors("demo", text, []), [])

    def test_marker_is_reported_by_marker_errors_not_guard_errors(self):
        text = "---\nname: demo\ndescription: d\n---\n::: claude\nx\n:::\n"
        self.assertEqual(sync.guard_errors("demo", text, []), [])
        self.assertTrue(sync.marker_errors("demo", text))

    def test_parse_frontmatter_folded_scalar_reads_full_value(self):
        text = (
            "---\n"
            "name: demo\n"
            "description: >\n"
            "  First folded line.\n"
            "  Second folded line.\n"
            "---\nbody\n"
        )
        self.assertEqual(
            sync.parse_frontmatter(text)["description"],
            "First folded line. Second folded line.",
        )

    def test_parse_frontmatter_literal_scalar_reads_full_value(self):
        text = "---\nname: demo\ndescription: |-\n  one\n  two\n---\nbody\n"
        self.assertEqual(sync.parse_frontmatter(text)["description"], "one two")

    def test_folded_description_over_1024_chars_is_an_error(self):
        folded = "".join(f"  {'x' * 80}\n" for _ in range(14))
        text = "---\nname: demo\ndescription: >\n" + folded + "---\nbody\n"
        errors = sync.guard_errors("demo", text, [])
        self.assertTrue(any("max 1024" in e for e in errors))

    def test_parse_frontmatter_plain_multiline_value_joined(self):
        text = (
            "---\n"
            "name: demo\n"
            "description: starts here\n"
            "  and continues\n"
            "  across lines\n"
            "---\nbody\n"
        )
        self.assertEqual(
            sync.parse_frontmatter(text)["description"],
            "starts here and continues across lines",
        )

    def test_parse_frontmatter_fence_with_trailing_whitespace_terminates(self):
        text = "---\nname: demo\n--- \nname: hijack\n"
        self.assertEqual(sync.parse_frontmatter(text), {"name": "demo"})

    def test_parse_frontmatter_without_closing_fence_returns_empty(self):
        self.assertEqual(sync.parse_frontmatter("---\nname: demo\n"), {})

    def test_parse_frontmatter_does_not_absorb_body_keys(self):
        text = "---\nname: demo\n---\nbody\nstatus: hijacked\n"
        self.assertEqual(sync.parse_frontmatter(text), {"name": "demo"})

    def test_parse_frontmatter_strips_only_balanced_quotes(self):
        text = "---\nname: \"demo\"\ndescription: don't do 'this'\n---\nbody\n"
        parsed = sync.parse_frontmatter(text)
        self.assertEqual(parsed["name"], "demo")
        self.assertEqual(parsed["description"], "don't do 'this'")

    def test_personal_string_error_includes_line_number(self):
        text = "---\nname: demo\ndescription: d\n---\nbody\nSee ~/ac/nono here.\n"
        errors = sync.guard_errors("demo", text, [])
        self.assertTrue(any("SKILL.md:6" in e for e in errors))

    def test_parse_frontmatter_folded_scalar_with_chomping(self):
        text = "---\nname: demo\ndescription: >-\n  one\n  two\n---\nbody\n"
        self.assertEqual(sync.parse_frontmatter(text)["description"], "one two")

    def test_parse_frontmatter_folded_scalar_with_indentation_indicator(self):
        text = "---\nname: demo\ndescription: >2\n  one\n  two\n---\nbody\n"
        self.assertEqual(sync.parse_frontmatter(text)["description"], "one two")

    def test_parse_frontmatter_empty_value_does_not_swallow_next_key(self):
        text = "---\nname: demo\ndescription:\nversion: 3\n---\nbody\n"
        parsed = sync.parse_frontmatter(text)
        self.assertEqual(parsed["description"], "")
        self.assertEqual(parsed["version"], "3")

    def test_parse_frontmatter_indented_mapping_leaves_other_keys_intact(self):
        text = (
            "---\n"
            "name: demo\n"
            "metadata:\n"
            "  author: x\n"
            "  tags: a\n"
            "description: real one\n"
            "---\nbody\n"
        )
        parsed = sync.parse_frontmatter(text)
        self.assertEqual(parsed["name"], "demo")
        self.assertEqual(parsed["description"], "real one")


class MarkerTest(unittest.TestCase):
    def test_marker_inside_backtick_fence_is_not_an_error(self):
        text = "body\n```markdown\n::: claude\ncontent\n:::\n```\nafter\n"
        self.assertEqual(sync.marker_errors("demo", text), [])

    def test_marker_outside_fence_is_an_error(self):
        text = "body\n::: claude\ncontent\n:::\n"
        errors = sync.marker_errors("demo", text)
        self.assertTrue(any("demo" in e and ":::" in e for e in errors))

    def test_marker_inside_tilde_fence_is_not_an_error(self):
        text = "body\n~~~\n::: claude\n~~~\nafter\n"
        self.assertEqual(sync.marker_errors("demo", text), [])

    def test_indented_fence_lines_still_open_and_close(self):
        text = "body\n  ```\n::: claude\n  ```\nafter\n"
        self.assertEqual(sync.marker_errors("demo", text), [])

    def test_marker_after_a_closed_fence_is_an_error(self):
        text = "```\nsafe\n```\n::: claude\n"
        self.assertTrue(sync.marker_errors("demo", text))


class TreeGuardTest(unittest.TestCase):
    def _write_skill(self, skills_dir, name):
        skill_dir = skills_dir / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: A clean skill.\n---\nbody\n",
            encoding="utf-8",
        )
        return skill_dir

    def test_supporting_file_referencing_private_skill_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            skill_dir = self._write_skill(tree / "skills", "demo")
            (skill_dir / "reference.md").write_text(
                "Intro line.\nRun `aiconf` first.\n", encoding="utf-8"
            )
            errors = sync.tree_guard_errors(tree, ["aiconf"])
            self.assertTrue(
                any(
                    "demo/reference.md:2: references unpublished skill 'aiconf'" in e
                    for e in errors
                )
            )

    def test_line_start_reference_gets_the_right_line_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            skill_dir = self._write_skill(tree / "skills", "demo")
            (skill_dir / "reference.md").write_text(
                "Intro line.\nSecond line.\n/aiconf is here.\n", encoding="utf-8"
            )
            errors = sync.tree_guard_errors(tree, ["aiconf"])
            self.assertTrue(
                any(
                    "demo/reference.md:3: references unpublished skill 'aiconf'" in e
                    for e in errors
                )
            )

    def test_every_reference_occurrence_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            skill_dir = self._write_skill(tree / "skills", "demo")
            (skill_dir / "reference.md").write_text(
                "Run `aiconf` first.\nThen `aiconf` again.\n", encoding="utf-8"
            )
            errors = sync.tree_guard_errors(tree, ["aiconf"])
            hits = [e for e in errors if "references unpublished skill" in e]
            self.assertEqual(len(hits), 2)

    def test_supporting_file_personal_string_error_includes_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            skill_dir = self._write_skill(tree / "skills", "demo")
            (skill_dir / "notes.md").write_text(
                "clean line\nsee /Users/nielsmadan/x\n", encoding="utf-8"
            )
            errors = sync.tree_guard_errors(tree, [])
            self.assertTrue(
                any("demo/notes.md:2: personal string" in e for e in errors)
            )

    def test_skill_directory_without_skill_md_is_an_error_not_an_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            skills_dir = tree / "skills"
            self._write_skill(skills_dir, "good")
            (skills_dir / "broken").mkdir()
            errors = sync.tree_guard_errors(tree, [])
            self.assertTrue(any("broken" in e and "SKILL.md" in e for e in errors))
            self.assertFalse(any("good" in e for e in errors))

    def test_missing_skills_directory_is_a_single_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors = sync.tree_guard_errors(Path(tmp), [])
            self.assertEqual(len(errors), 1)


class RenderTest(unittest.TestCase):
    def test_swap_banner_replaces_loadout_banner(self):
        text = (
            "---\nname: demo\n---\n\n"
            "<!-- Generated by loadout from skills/demo/. Edits here are replaced"
            " on the next sync. -->\n\nbody\n"
        )
        result = sync.swap_banner(text)
        self.assertNotIn("loadout", result)
        self.assertIn("github.com/nielsmadan/agentic-coding", result)

    def test_swap_banner_leaves_text_without_a_banner_alone(self):
        text = "---\nname: demo\n---\n\nbody\n"
        self.assertEqual(sync.swap_banner(text), text)

    def test_render_tree_writes_selected_skills_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src"
            (source / "keep").mkdir(parents=True)
            (source / "keep" / "SKILL.md").write_text("KEEP", encoding="utf-8")
            (source / "drop").mkdir(parents=True)
            (source / "drop" / "SKILL.md").write_text("DROP", encoding="utf-8")
            skills = [
                FakeSkill("keep", source / "keep" / "SKILL.md", ()),
                FakeSkill("drop", source / "drop" / "SKILL.md", ()),
            ]
            out = root / "out"
            out.mkdir()
            sync.render_tree(out, ["keep"], skills, lambda s, h: f"rendered:{s.name}")
            self.assertTrue((out / "skills" / "keep" / "SKILL.md").is_file())
            self.assertFalse((out / "skills" / "drop").exists())
            self.assertEqual(
                (out / "skills" / "keep" / "SKILL.md").read_text(encoding="utf-8"),
                "rendered:keep",
            )

    def test_render_tree_copies_supporting_files_preserving_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "src" / "demo"
            (skill_dir / "scripts").mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("x", encoding="utf-8")
            script = skill_dir / "scripts" / "run.sh"
            script.write_text("#!/bin/sh\n", encoding="utf-8")
            script.chmod(0o755)
            out = root / "out"
            out.mkdir()
            skills = [
                FakeSkill(
                    "demo", skill_dir / "SKILL.md", (Path("scripts/run.sh"),)
                )
            ]
            sync.render_tree(out, ["demo"], skills, lambda s, h: "x")
            copied = out / "skills" / "demo" / "scripts" / "run.sh"
            self.assertTrue(copied.is_file())
            self.assertTrue(copied.stat().st_mode & 0o111)

    def test_load_loadout_reports_shadowed_package_as_guidance(self):
        # The namespace-package shadow raises plain ImportError ("cannot import
        # name ... (unknown location)"), not ModuleNotFoundError — the handler
        # must turn that into guidance, not a traceback.
        shadow = ImportError(
            "cannot import name 'discover_skills' from 'loadout.skills' "
            "(unknown location)"
        )
        with unittest.mock.patch("builtins.__import__", side_effect=shadow):
            with self.assertRaises(SystemExit) as ctx:
                sync.load_loadout()
        self.assertIn("not importable", str(ctx.exception))

    def test_render_tree_preserves_github_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "src" / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("x", encoding="utf-8")
            out = root / "out"
            (out / ".github" / "workflows").mkdir(parents=True)
            keeper = out / ".github" / "workflows" / "sync.yml"
            keeper.write_text("name: sync\n", encoding="utf-8")
            (out / "skills" / "stale").mkdir(parents=True)
            skills = [FakeSkill("demo", skill_dir / "SKILL.md", ())]
            sync.render_tree(out, ["demo"], skills, lambda s, h: "x")
            self.assertTrue(keeper.is_file())
            self.assertFalse((out / "skills" / "stale").exists())

    def test_render_tree_rejects_absolute_supporting_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "src" / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("x", encoding="utf-8")
            out = root / "out"
            out.mkdir()
            skills = [
                FakeSkill("demo", skill_dir / "SKILL.md", (Path("/etc/passwd"),))
            ]
            with self.assertRaises(ValueError) as ctx:
                sync.render_tree(out, ["demo"], skills, lambda s, h: "x")
            self.assertIn("escapes the skill directory", str(ctx.exception))

    def test_render_tree_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "src" / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("x", encoding="utf-8")
            (root / "src" / "secret.md").write_text("s", encoding="utf-8")
            out = root / "out"
            out.mkdir()
            skills = [
                FakeSkill("demo", skill_dir / "SKILL.md", (Path("../secret.md"),))
            ]
            with self.assertRaises(ValueError) as ctx:
                sync.render_tree(out, ["demo"], skills, lambda s, h: "x")
            self.assertIn("escapes the skill directory", str(ctx.exception))

    def test_render_tree_rejects_symlinked_supporting_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "src" / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("x", encoding="utf-8")
            real = root / "outside.md"
            real.write_text("real", encoding="utf-8")
            (skill_dir / "link.md").symlink_to(real)
            out = root / "out"
            out.mkdir()
            skills = [FakeSkill("demo", skill_dir / "SKILL.md", (Path("link.md"),))]
            with self.assertRaises(ValueError) as ctx:
                sync.render_tree(out, ["demo"], skills, lambda s, h: "x")
            self.assertIn("symlinked supporting file refused", str(ctx.exception))


def _banner_render(skill, harness):
    return (
        f"---\nname: {skill.name}\ndescription: A clean skill.\n---\n\n"
        f"<!-- Generated by loadout from skills/{skill.name}/. Edits here are "
        "replaced on the next sync. -->\n\nbody\n"
    )


class BuildTest(unittest.TestCase):
    def _setup(self, tmp, publish, skill_names):
        root = Path(tmp)
        manifest = root / "skills.toml"
        listed = ", ".join(f'"{name}"' for name in publish)
        manifest.write_text(
            f"private = []\n[groups]\nAll = [{listed}]\n", encoding="utf-8"
        )
        skills_root = root / "src"
        for name in skill_names:
            skill_dir = skills_root / name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("source", encoding="utf-8")
        out = root / "out"
        out.mkdir()
        return manifest, skills_root, out

    def _loader(self, skills_root, names, render=_banner_render):
        def discover(root):
            return [
                FakeSkill(name, skills_root / name / "SKILL.md", ()) for name in names
            ]

        return lambda: (discover, render)

    def test_manifest_error_returns_early_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest, skills_root, out = self._setup(tmp, ["alpha", "ghost"], ["alpha"])
            called = []

            def loader():
                called.append(True)
                return (lambda root: [], _banner_render)

            errors, warnings = sync.build(
                out, manifest_path=manifest, skills_root=skills_root, loader=loader
            )
            self.assertTrue(any("no such skill" in e for e in errors))
            self.assertEqual(warnings, [])
            self.assertEqual(called, [])
            self.assertFalse((out / "skills").exists())
            self.assertFalse((out / "README.md").exists())

    def test_happy_path_writes_sorted_artifacts_without_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest, skills_root, out = self._setup(
                tmp, ["beta", "alpha"], ["alpha", "beta"]
            )
            errors, warnings = sync.build(
                out,
                manifest_path=manifest,
                skills_root=skills_root,
                loader=self._loader(skills_root, ["alpha", "beta"]),
            )
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])
            for name in ("alpha", "beta"):
                document = out / "skills" / name / "SKILL.md"
                self.assertTrue(document.is_file())
                self.assertIn(
                    sync.PROVENANCE, document.read_text(encoding="utf-8")
                )
            for relative in (
                "README.md",
                "LICENSE",
                ".claude-plugin/marketplace.json",
                ".claude-plugin/plugin.json",
            ):
                self.assertTrue((out / relative).is_file(), relative)
            readme = (out / "README.md").read_text(encoding="utf-8")
            self.assertLess(readme.index("`alpha`"), readme.index("`beta`"))

    def test_skill_missing_from_discover_is_an_error_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest, skills_root, out = self._setup(
                tmp, ["alpha", "ghost"], ["alpha", "ghost"]
            )
            errors, _ = sync.build(
                out,
                manifest_path=manifest,
                skills_root=skills_root,
                loader=self._loader(skills_root, ["alpha"]),
            )
            self.assertIn(
                "ghost: not rendered (missing from discover_skills output)", errors
            )

    def test_render_without_banner_is_a_provenance_error(self):
        def render(skill, harness):
            return f"---\nname: {skill.name}\ndescription: d\n---\n\nbody\n"

        with tempfile.TemporaryDirectory() as tmp:
            manifest, skills_root, out = self._setup(tmp, ["alpha"], ["alpha"])
            errors, _ = sync.build(
                out,
                manifest_path=manifest,
                skills_root=skills_root,
                loader=self._loader(skills_root, ["alpha"], render),
            )
            self.assertIn("alpha: missing provenance header", errors)

    def test_out_of_fence_marker_in_render_is_an_error(self):
        def render(skill, harness):
            return _banner_render(skill, harness) + "::: claude\nx\n:::\n"

        with tempfile.TemporaryDirectory() as tmp:
            manifest, skills_root, out = self._setup(tmp, ["alpha"], ["alpha"])
            errors, warnings = sync.build(
                out,
                manifest_path=manifest,
                skills_root=skills_root,
                loader=self._loader(skills_root, ["alpha"], render),
            )
            self.assertTrue(
                any("still contains ::: harness markers" in e for e in errors)
            )
            self.assertEqual(warnings, [])


class SourceErrorsTest(unittest.TestCase):
    def _setup(self, tmp, publish):
        root = Path(tmp)
        manifest = root / "skills.toml"
        listed = ", ".join(f'"{name}"' for name in publish)
        manifest.write_text(
            f"private = []\n[groups]\nAll = [{listed}]\n", encoding="utf-8"
        )
        skills_root = root / "src"
        skills_root.mkdir()
        return manifest, skills_root

    def test_personal_string_in_source_skill_md_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest, skills_root = self._setup(tmp, ["demo"])
            skill_dir = skills_root / "demo"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "line one\nsee ~/ac/nono here\n", encoding="utf-8"
            )
            errors = sync.source_errors(
                manifest_path=manifest, skills_root=skills_root
            )
            self.assertTrue(
                any("demo/SKILL.md:2: personal string" in e for e in errors)
            )

    def test_personal_string_in_supporting_file_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest, skills_root = self._setup(tmp, ["demo"])
            skill_dir = skills_root / "demo" / "refs"
            skill_dir.mkdir(parents=True)
            (skills_root / "demo" / "SKILL.md").write_text("clean\n", encoding="utf-8")
            (skill_dir / "notes.md").write_text(
                "a\nb\n/Users/nielsmadan/x\n", encoding="utf-8"
            )
            errors = sync.source_errors(
                manifest_path=manifest, skills_root=skills_root
            )
            self.assertTrue(
                any("demo/refs/notes.md:3: personal string" in e for e in errors)
            )

    def test_markers_and_private_references_in_source_are_not_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest, skills_root = self._setup(tmp, ["demo"])
            skill_dir = skills_root / "demo"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: other\n---\n::: claude\nRun `aiconf` first.\n:::\n",
                encoding="utf-8",
            )
            self.assertEqual(
                sync.source_errors(manifest_path=manifest, skills_root=skills_root),
                [],
            )


class MainTest(unittest.TestCase):
    def _run_main(self, argv):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                sync.main(argv)
        return ctx.exception.code

    def test_empty_out_does_not_render_into_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                code = self._run_main(["--out", ""])
            finally:
                os.chdir(cwd)
            self.assertEqual(code, 2)
            self.assertFalse((Path(tmp) / "skills").exists())

    def test_out_and_check_manifest_are_mutually_exclusive(self):
        code = self._run_main(["--check-manifest", "--out", "somewhere"])
        self.assertEqual(code, 2)

    def test_out_and_check_sources_are_mutually_exclusive(self):
        code = self._run_main(["--check-sources", "--out", "somewhere"])
        self.assertEqual(code, 2)


class ArtifactTest(unittest.TestCase):
    def test_marketplace_has_no_version_and_root_source(self):
        market = sync.build_marketplace()
        self.assertEqual(market["name"], "nlsmdn")
        self.assertEqual(len(market["plugins"]), 1)
        plugin = market["plugins"][0]
        self.assertEqual(plugin["name"], "nlsmdn")
        self.assertEqual(plugin["source"], "./")
        self.assertNotIn("version", plugin)

    def test_owner_carries_url_not_email(self):
        market = sync.build_marketplace()
        self.assertEqual(market["owner"]["url"], "https://github.com/nielsmadan")
        self.assertNotIn("email", market["owner"])

    def test_plugin_manifest_omits_version(self):
        plugin = sync.build_plugin()
        self.assertEqual(plugin["name"], "nlsmdn")
        self.assertEqual(plugin["license"], "MIT")
        self.assertNotIn("version", plugin)

    def test_readme_lists_every_skill(self):
        readme = sync.build_readme(
            [("Core", [("alpha", "Does alpha."), ("beta", "Does beta.")])]
        )
        self.assertIn("alpha", readme)
        self.assertIn("Does beta.", readme)
        self.assertIn("claude plugin marketplace add nielsmadan/skills", readme)
        self.assertIn("npx skills add nielsmadan/skills", readme)

    def test_readme_states_the_auto_update_caveat(self):
        readme = sync.build_readme([("Core", [("alpha", "Does alpha.")])])
        self.assertIn("auto-update", readme.lower())

    def test_readme_renders_one_section_per_group(self):
        readme = sync.build_readme(
            [
                ("Code review", [("alpha", "Does alpha.")]),
                ("Docs & writing", [("beta", "Does beta."), ("gamma", "Does gamma.")]),
            ]
        )
        self.assertIn("### Code review", readme)
        self.assertIn("### Docs & writing", readme)
        self.assertIn("| `alpha` | Does alpha. |", readme)
        self.assertIn("3 skills", readme)

    def test_write_artifacts_creates_all_four_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            sync.write_artifacts(out, [("Core", [("alpha", "Does alpha.")])])
            for relative in (
                ".claude-plugin/marketplace.json",
                ".claude-plugin/plugin.json",
                "LICENSE",
                "README.md",
            ):
                self.assertTrue((out / relative).is_file(), relative)



class MarkerFenceTest(unittest.TestCase):
    def test_unbalanced_fence_is_an_error(self):
        text = "# doc\n\n```\nunterminated\n"
        errors = sync.marker_errors("demo", text)
        self.assertIn("unbalanced code fence", errors[0])

    def test_marker_after_unclosed_fence_still_fails(self):
        text = "```\nopen\n\n::: claude\nleaked\n:::\n"
        self.assertTrue(sync.marker_errors("demo", text))


class RenderEscapeTest(unittest.TestCase):
    def test_directory_symlink_escape_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root / "outside"
            outside.mkdir()
            (outside / "secret.md").write_text("s", encoding="utf-8")
            skill_dir = root / "src" / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("x", encoding="utf-8")
            (skill_dir / "references").symlink_to(outside)
            out = root / "out"
            out.mkdir()
            skills = [
                FakeSkill(
                    "demo",
                    skill_dir / "SKILL.md",
                    (Path("references/secret.md"),),
                )
            ]
            with self.assertRaises(ValueError) as ctx:
                sync.render_tree(out, ["demo"], skills, lambda s, h: "x")
            self.assertIn("escapes the skill directory", str(ctx.exception))

    def test_build_reports_render_escape_as_error_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "skills.toml"
            manifest.write_text(
                'private = []\n[groups]\nAll = ["demo"]\n', encoding="utf-8"
            )
            src = root / "skills"
            skill_dir = src / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo\ndescription: d\n---\nbody\n", encoding="utf-8"
            )
            skills = [
                FakeSkill("demo", skill_dir / "SKILL.md", (Path("/etc/passwd"),))
            ]
            loader = lambda: (lambda r: skills, lambda s, h: "x")
            out = root / "out"
            out.mkdir()
            errors, warnings = sync.build(
                out, manifest_path=manifest, skills_root=src, loader=loader
            )
            self.assertTrue(any("escapes the skill directory" in e for e in errors))

    def test_failed_build_does_not_write_readme(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "skills.toml"
            manifest.write_text(
                'private = []\n[groups]\nAll = ["demo", "ghostless"]\n',
                encoding="utf-8"
            )
            src = root / "skills"
            for name in ("demo", "ghostless"):
                d = src / name
                d.mkdir(parents=True)
                (d / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: d\n---\nbody\n",
                    encoding="utf-8",
                )
            rendered = sync.swap_banner(
                "---\nname: demo\ndescription: d\n---\n\n"
                "<!-- Generated by loadout from skills/demo/. Edits here are"
                " replaced on the next sync. -->\n\nbody\n"
            )
            skills = [FakeSkill("demo", src / "demo" / "SKILL.md", ())]
            loader = lambda: (lambda r: skills, lambda s, h: rendered)
            out = root / "out"
            out.mkdir()
            errors, _ = sync.build(
                out, manifest_path=manifest, skills_root=src, loader=loader
            )
            self.assertTrue(any("ghostless: not rendered" in e for e in errors))
            self.assertFalse((out / "README.md").exists())


class SourceErrorsMissingDirTest(unittest.TestCase):
    def test_missing_skill_directory_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "skills.toml"
            manifest.write_text(
                'private = []\n[groups]\nAll = ["ghost"]\n', encoding="utf-8"
            )
            errors = sync.source_errors(
                manifest_path=manifest, skills_root=root / "skills"
            )
            self.assertTrue(any("ghost: no such skill directory" in e for e in errors))


class RealTreeTest(unittest.TestCase):
    def test_live_tree_is_fully_classified(self):
        self.assertEqual(sync.check_manifest(), [])

    def test_live_publish_sources_carry_no_personal_strings(self):
        self.assertEqual(sync.source_errors(), [])

    def test_check_flags_compose(self):
        self.assertEqual(sync.main(["--check-manifest", "--check-sources"]), 0)


if __name__ == "__main__":
    unittest.main()
