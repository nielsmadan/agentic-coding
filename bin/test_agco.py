from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("agco")
LOADER = importlib.machinery.SourceFileLoader("agco", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
agco = importlib.util.module_from_spec(SPEC)
sys.modules[LOADER.name] = agco
LOADER.exec_module(agco)


class AgcoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.roots = agco.Roots(
            claude_projects=root / "claude" / "projects",
            codex_sessions=root / "codex" / "sessions",
            opencode_db=root / "opencode" / "opencode.db",
            pi_sessions=root / "pi" / "sessions",
        )
        self.cwd = "/Users/tester/wrksp/app"
        self.other = "/Users/tester/wrksp/other"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_jsonl(self, path: Path, records: list[dict], mtime: float) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(record) + "\n" for record in records))
        os.utime(path, (mtime, mtime))
        return path

    def write_claude(self, cwd: str, name: str, mtime: float) -> Path:
        directory = self.roots.claude_projects / agco.CLCOF.project_slug(cwd)
        return self.write_jsonl(directory / name, [{"type": "custom-title"}], mtime)

    def write_codex(self, cwd: str, name: str, mtime: float) -> Path:
        record = {"type": "session_meta", "payload": {"id": name, "cwd": cwd}}
        return self.write_jsonl(
            self.roots.codex_sessions / "2026" / "08" / name, [record], mtime
        )

    def write_pi(
        self, cwd: str, name: str, mtime: float, extra: list[dict] | None = None
    ) -> Path:
        record = {"type": "session", "id": name, "cwd": cwd}
        return self.write_jsonl(
            self.roots.pi_sessions / "slug" / name, [record] + (extra or []), mtime
        )

    def write_opencode(self, cwd: str, session_id: str, updated_ms: int) -> None:
        self.roots.opencode_db.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.roots.opencode_db)
        try:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS session "
                "(id TEXT, directory TEXT, title TEXT, time_created INTEGER, time_updated INTEGER)"
            )
            connection.execute(
                "INSERT INTO session VALUES (?, ?, ?, ?, ?)",
                (session_id, cwd, "title", updated_ms, updated_ms),
            )
            connection.commit()
        finally:
            connection.close()

    def test_no_sessions_anywhere(self) -> None:
        self.assertIsNone(agco.most_recent_agent(self.cwd, self.roots))

    def test_claude_matches_by_project_slug(self) -> None:
        self.write_claude(self.cwd, "a.jsonl", 1000)
        self.write_claude(self.other, "b.jsonl", 5000)
        self.assertEqual(agco.claude_latest(self.cwd, self.roots), 1000)

    def test_codex_ignores_other_directories(self) -> None:
        self.write_codex(self.other, "newer.jsonl", 9000)
        self.write_codex(self.cwd, "older.jsonl", 1000)
        self.assertEqual(agco.codex_latest(self.cwd, self.roots), 1000)
        self.assertIsNone(agco.codex_latest("/nowhere", self.roots))

    def test_pi_takes_newest_matching_session(self) -> None:
        self.write_pi(self.cwd, "old.jsonl", 1000)
        self.write_pi(self.cwd, "new.jsonl", 4000)
        self.write_pi(self.other, "newest.jsonl", 9000)
        self.assertEqual(agco.pi_latest(self.cwd, self.roots), 4000)

    def test_pi_provider_takes_the_last_switch(self) -> None:
        self.write_pi(
            self.cwd,
            "s.jsonl",
            1000,
            [
                {"type": "model_change", "provider": "openrouter", "modelId": "glm"},
                {"type": "model_change", "provider": "openai-codex", "modelId": "sol"},
            ],
        )
        self.assertEqual(agco.pi_provider(self.cwd, self.roots), "openai-codex")

    def test_pi_provider_reads_assistant_messages(self) -> None:
        self.write_pi(
            self.cwd,
            "s.jsonl",
            1000,
            [
                {"type": "model_change", "provider": "openai-codex", "modelId": "sol"},
                {"type": "message", "message": {"role": "assistant", "provider": "openrouter"}},
            ],
        )
        self.assertEqual(agco.pi_provider(self.cwd, self.roots), "openrouter")

    def test_pi_provider_uses_newest_matching_session(self) -> None:
        self.write_pi(
            self.cwd,
            "old.jsonl",
            1000,
            [{"type": "model_change", "provider": "openrouter", "modelId": "glm"}],
        )
        self.write_pi(
            self.cwd,
            "new.jsonl",
            4000,
            [{"type": "model_change", "provider": "openai-codex", "modelId": "sol"}],
        )
        self.write_pi(
            self.other,
            "newest.jsonl",
            9000,
            [{"type": "model_change", "provider": "openrouter", "modelId": "glm"}],
        )
        self.assertEqual(agco.pi_provider(self.cwd, self.roots), "openai-codex")

    def test_pi_provider_absent_when_session_records_none(self) -> None:
        self.write_pi(self.cwd, "s.jsonl", 1000)
        self.assertIsNone(agco.pi_provider(self.cwd, self.roots))

    def test_opencode_reads_time_updated(self) -> None:
        self.write_opencode(self.cwd, "s1", 2_000_000)
        self.write_opencode(self.cwd, "s2", 7_000_000)
        self.write_opencode(self.other, "s3", 9_000_000)
        self.assertEqual(agco.opencode_latest(self.cwd, self.roots), 7000.0)

    def test_opencode_missing_database(self) -> None:
        self.assertIsNone(agco.opencode_latest(self.cwd, self.roots))

    def test_picks_newest_across_agents(self) -> None:
        self.write_claude(self.cwd, "a.jsonl", 1000)
        self.write_codex(self.cwd, "b.jsonl", 3000)
        self.write_pi(self.cwd, "c.jsonl", 2000)
        self.write_opencode(self.cwd, "s1", 2_500_000)
        self.assertEqual(agco.most_recent_agent(self.cwd, self.roots), ("codex", 3000))

    def test_opencode_can_win(self) -> None:
        self.write_claude(self.cwd, "a.jsonl", 1000)
        self.write_opencode(self.cwd, "s1", 8_000_000)
        agent, _ = agco.most_recent_agent(self.cwd, self.roots)
        self.assertEqual(agent, "opencode")

    def test_human_age(self) -> None:
        self.assertEqual(agco.human_age(-5), "0s ago")
        self.assertEqual(agco.human_age(30), "30s ago")
        self.assertEqual(agco.human_age(12 * 60), "12m ago")
        self.assertEqual(agco.human_age(5 * 3600), "5h ago")
        self.assertEqual(agco.human_age(4 * 86400), "4d ago")


if __name__ == "__main__":
    unittest.main()
