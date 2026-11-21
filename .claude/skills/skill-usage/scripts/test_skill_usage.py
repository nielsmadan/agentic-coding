from __future__ import annotations

import importlib.util
import io
import json
import sqlite3
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


def devin_message(role: str, content: str, source: str, **extra) -> dict:
    metadata = {"created_at": "2026-10-04T00:00:00Z", "telemetry": {"source": source},
                **extra.pop("metadata", {})}
    return {"role": role, "content": content, "metadata": metadata, **extra}


def devin_skill_call(skill: str) -> dict:
    return devin_message("assistant", "", "assistant",
                         tool_calls=[{"name": "skill", "arguments": {"skill": skill}}])


def devin_prompt(typed: str, content: str) -> dict:
    return devin_message("user", content, "user", metadata={
        "is_user_input": True,
        "extensions": {"chisel/acp-content-blocks": [{"type": "text", "text": typed}]}})


def make_devin_db(path: Path, cwd: str) -> None:
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE sessions (id TEXT PRIMARY KEY, working_directory TEXT, title TEXT,
            created_at INTEGER, last_activity_at INTEGER, main_chain_id INTEGER);
        CREATE TABLE message_nodes (session_id TEXT, node_id INTEGER, parent_node_id INTEGER,
            chat_message TEXT, created_at INTEGER);
        CREATE TABLE subagent_heads (session_id TEXT, agent_id TEXT, chain_node_id INTEGER,
            updated_at INTEGER);
    """)
    connection.execute("INSERT INTO sessions VALUES ('dv1', ?, 't', 1790000000, 1790000100, 2)",
                       (cwd,))
    connection.execute("INSERT INTO subagent_heads VALUES ('dv1', 'sidekick', 4, 1790000100)")
    nodes = [(0, None, devin_prompt("/devin:plan go", "plan body\ngo")),
             (1, 0, devin_skill_call("qa")),
             (2, 0, devin_skill_call("qa")),
             (3, None, devin_message("user", "handoff", "subagent_task")),
             (4, 3, devin_skill_call("nono-sandbox"))]
    connection.executemany("INSERT INTO message_nodes VALUES ('dv1', ?, ?, ?, 1790000000)",
                           [(n, parent, json.dumps(m)) for n, parent, m in nodes])
    connection.commit()
    connection.close()


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

    def test_devin_counts_skill_tool_and_expanded_slash_prompt(self):
        self.assertEqual(su.devin_skills(devin_skill_call("qa")), [("qa", "model")])
        self.assertEqual(su.devin_skills(devin_prompt("/devin:plan go", "plan body\ngo")),
                         [("plan", "user")])

    def test_devin_ignores_a_builtin_slash_command_left_unexpanded(self):
        self.assertEqual(su.devin_skills(devin_prompt("/compact", "/compact")), [])

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
                                 codex_sessions=root / "codex", cursor_projects=root / "cursor",
                                 cursor_chats=root / "cursor-chats", devin_db=root / "devin.db",
                                 droid_sessions=root / "droid",
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

    def test_report_counts_devin_kept_chains_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roots = su.sal.Roots(claude_projects=root / "claude", claude_archive=root / "archive",
                                 codex_sessions=root / "codex", cursor_projects=root / "cursor",
                                 cursor_chats=root / "cursor-chats", devin_db=root / "devin.db",
                                 droid_sessions=root / "droid", opencode_db=root / "oc.db",
                                 pi_sessions=root / "pi")
            make_devin_db(roots.devin_db, f"{HOME}/proj")

            out = io.StringIO()
            with redirect_stdout(out):
                code = su.main(["--days", "0", "--devin", "--format", "json"], roots=roots)

        report = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(report["incomplete"], [])
        self.assertEqual(
            sorted((r["skill"], r["invocations"], r["user"], r["model"], r["by_agent"]["devin"])
                   for r in report["skills"]),
            [("nono-sandbox", 1, 0, 1, 1), ("plan", 1, 1, 0, 1), ("qa", 1, 0, 1, 1)])


if __name__ == "__main__":
    unittest.main()
