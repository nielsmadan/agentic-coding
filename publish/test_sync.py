import tempfile
import unittest
import unittest.mock
from pathlib import Path

from publish import sync


class ManifestTest(unittest.TestCase):
    def test_load_manifest_reads_both_lists(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "skills.toml"
            path.write_text('publish = ["a", "b"]\nprivate = ["c"]\n', encoding="utf-8")
            publish, private = sync.load_manifest(path)
            self.assertEqual(publish, ["a", "b"])
            self.assertEqual(private, ["c"])

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

    def test_marker_is_a_warning_not_an_error(self):
        text = "---\nname: demo\ndescription: d\n---\n::: claude\nx\n:::\n"
        self.assertEqual(sync.guard_errors("demo", text, []), [])
        self.assertTrue(sync.marker_warnings("demo", text))

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
                sync.FakeSkill("keep", source / "keep" / "SKILL.md", ()),
                sync.FakeSkill("drop", source / "drop" / "SKILL.md", ()),
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
                sync.FakeSkill(
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
            skills = [sync.FakeSkill("demo", skill_dir / "SKILL.md", ())]
            sync.render_tree(out, ["demo"], skills, lambda s, h: "x")
            self.assertTrue(keeper.is_file())
            self.assertFalse((out / "skills" / "stale").exists())


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
        readme = sync.build_readme([("alpha", "Does alpha."), ("beta", "Does beta.")])
        self.assertIn("alpha", readme)
        self.assertIn("Does beta.", readme)
        self.assertIn("claude plugin marketplace add nielsmadan/skills", readme)
        self.assertIn("npx skills add nielsmadan/skills", readme)

    def test_readme_states_the_auto_update_caveat(self):
        readme = sync.build_readme([("alpha", "Does alpha.")])
        self.assertIn("auto-update", readme.lower())

    def test_write_artifacts_creates_all_four_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            sync.write_artifacts(out, [("alpha", "Does alpha.")])
            for relative in (
                ".claude-plugin/marketplace.json",
                ".claude-plugin/plugin.json",
                "LICENSE",
                "README.md",
            ):
                self.assertTrue((out / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
