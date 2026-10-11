from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("skill_usage", Path(__file__).with_name("skill_usage.py"))
su = importlib.util.module_from_spec(SPEC)
sys.modules["skill_usage"] = su
SPEC.loader.exec_module(su)

HOME = "/Users/someone"


def claude_meta(skill_path: str, tool_use: str | None = None) -> dict:
    record = {"type": "user", "isMeta": True, "cwd": f"{HOME}/proj",
              "timestamp": "2026-10-01T10:00:00Z",
              "message": {"content": [{"type": "text",
                                       "text": f"Base directory for this skill: {skill_path}\n\nbody"}]}}
    if tool_use:
        record["sourceToolUseID"] = tool_use
    return record


class DetectorTests(unittest.TestCase):
    def test_claude_separates_typed_and_model_invoked_loads(self):
        self.assertEqual(su.claude_skills(claude_meta(f"{HOME}/.claude/skills/commit")),
                         [("commit", "user")])
        self.assertEqual(su.claude_skills(claude_meta(f"{HOME}/.claude/skills/commit", "toolu_1")),
                         [("commit", "model")])

    def test_claude_ignores_a_builtin_slash_command(self):
        record = {"type": "user", "message": {"content":
                  "<command-name>/model</command-name> <command-message>model</command-message>"}}
        self.assertEqual(su.claude_skills(record), [])

    def test_codex_reads_dollar_skill_blocks_and_installed_skill_file_reads(self):
        typed = {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [
            {"type": "input_text", "text": "<skill>\n<name>commit</name>\n<path>x</path>"}]}}
        read = {"type": "response_item", "payload": {"type": "custom_tool_call", "input":
                f'exec_command({{cmd:"cat {HOME}/.codex/skills/code-review/SKILL.md {HOME}/.agents/skills/plan/SKILL.md"}})'}}
        source_edit = {"type": "response_item", "payload": {"type": "function_call", "arguments":
                       json.dumps({"cmd": f"cat {HOME}/ac/loadout/skills/commit/SKILL.md"})}}

        self.assertEqual(su.codex_skills(typed), [("commit", "user")])
        self.assertEqual(sorted(su.codex_skills(read)), [("code-review", "model"), ("plan", "model")])
        self.assertEqual(su.codex_skills(source_edit), [])

    def test_droid_counts_skill_tool_and_user_selection_but_not_tool_results(self):
        tool = {"type": "message", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": "code-review"}}]}}
        selected = {"type": "message", "message": {"role": "user", "content": [
            {"type": "text", "text": 'The user has selected: <skill name="qa" filePath="x">'}]}}
        result = {"type": "message", "message": {"role": "user", "content": [
            {"type": "tool_result", "content": 'Skill "qa" is now active. <skill name="qa">'}]}}

        self.assertEqual(su.droid_skills(tool), [("code-review", "model")])
        self.assertEqual(su.droid_skills(selected), [("qa", "user")])
        self.assertEqual(su.droid_skills(result), [])

    def test_pi_counts_skill_command_and_read_tool_on_installed_file(self):
        typed = {"type": "message", "message": {"role": "user", "content": [
            {"type": "text", "text": '<skill name="commit" location="/x/SKILL.md">'}]}}
        read = {"type": "message", "message": {"role": "assistant", "content": [
            {"type": "toolCall", "name": "read",
             "arguments": {"path": f"{HOME}/.pi/agent/git/github.com/o/r/skills/brainstorming/SKILL.md"}}]}}

        self.assertEqual(su.pi_skills(typed), [("commit", "user")])
        self.assertEqual(su.pi_skills(read), [("brainstorming", "model")])

    def test_opencode_reads_skill_tool_name(self):
        part = {"type": "tool", "tool": "skill", "state": {"input": {"name": "superpowers:plan"}}}
        self.assertEqual(su.opencode_skills(part), [("plan", "model")])


class AggregationTests(unittest.TestCase):
    def test_file_reads_count_once_per_session_but_invocations_all_count(self):
        events = [su.Event("codex", "s1", None, None, "code-review", "model"),
                  su.Event("codex", "s1", None, None, "code-review", "model"),
                  su.Event("codex", "s1", None, None, "commit", "user"),
                  su.Event("codex", "s1", None, None, "commit", "user"),
                  su.Event("claude", "s2", None, None, "commit", "model"),
                  su.Event("claude", "s2", None, None, "commit", "model")]

        kept = su.dedupe_reads(events)

        self.assertEqual([(e.agent, e.skill) for e in kept],
                         [("codex", "code-review"), ("codex", "commit"), ("codex", "commit"),
                          ("claude", "commit"), ("claude", "commit")])

    def test_summarize_ranks_by_sessions_and_splits_agents(self):
        events = [su.Event("claude", "a", None, "2026-10-02T00:00:00Z", "commit", "user"),
                  su.Event("claude", "a", None, "2026-10-01T00:00:00Z", "commit", "model"),
                  su.Event("codex", "b", None, "2026-09-01T00:00:00Z", "commit", "user"),
                  su.Event("codex", "c", None, None, "plan", "model")]

        rows = su.summarize(events, ["claude", "codex"])

        self.assertEqual(rows[0], {"skill": "commit", "sessions": 2, "invocations": 3,
                                   "user": 2, "model": 1, "by_agent": {"claude": 1, "codex": 1},
                                   "last_used": "2026-10-02"})
        self.assertEqual(rows[1]["skill"], "plan")

    def test_automation_cwds(self):
        self.assertTrue(su.is_automation("/private/var/folders/v_/x/T/demo"))
        self.assertTrue(su.is_automation("/tmp/run"))
        self.assertTrue(su.is_automation(f"{HOME}/wrksp/app/evals/runs/.sandbox/case-1"))
        self.assertFalse(su.is_automation(f"{HOME}/wrksp/app"))


class EndToEndTests(unittest.TestCase):
    def test_report_counts_claude_and_codex_and_excludes_automation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roots = su.sal.Roots(claude_projects=root / "claude", claude_archive=root / "archive",
                                 codex_sessions=root / "codex", droid_sessions=root / "droid",
                                 opencode_db=root / "oc.db", pi_sessions=root / "pi")
            proj = roots.claude_projects / "-p"
            proj.mkdir(parents=True)
            (proj / "s1.jsonl").write_text(json.dumps(claude_meta(f"{HOME}/.claude/skills/commit")) + "\n")
            sandboxed = dict(claude_meta(f"{HOME}/.claude/skills/use"), cwd="/tmp/eval")
            (proj / "s2.jsonl").write_text(json.dumps(sandboxed) + "\n")
            roots.codex_sessions.mkdir()
            (roots.codex_sessions / "r.jsonl").write_text("\n".join(json.dumps(r) for r in [
                {"type": "session_meta", "payload": {"id": "cx1", "cwd": f"{HOME}/proj"}},
                {"type": "response_item", "timestamp": "2026-10-03T00:00:00Z", "payload": {
                    "type": "message", "role": "user",
                    "content": [{"type": "input_text", "text": "<skill>\n<name>commit</name>"}]}},
            ]) + "\n")

            out = io.StringIO()
            with redirect_stdout(out):
                code = su.main(["--days", "0", "--claude", "--codex", "--format", "json"], roots=roots)

        report = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual([r["skill"] for r in report["skills"]], ["commit"])
        self.assertEqual(report["skills"][0]["by_agent"], {"claude": 1, "codex": 1})


if __name__ == "__main__":
    unittest.main()
