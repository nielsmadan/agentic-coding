from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("clcof")
LOADER = importlib.machinery.SourceFileLoader("clcof", str(MODULE_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
clcof = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(clcof)


class ClcofTests(unittest.TestCase):
    def write_transcript(
        self,
        home: Path,
        cwd: str,
        session_id: str,
        entries: list[dict],
        mtime: int,
    ) -> Path:
        directory = home / ".claude" / "projects" / clcof.project_slug(cwd)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{session_id}.jsonl"
        path.write_text("".join(json.dumps(entry) + "\n" for entry in entries))
        os.utime(path, (mtime, mtime))
        return path

    def write_registry(self, home: Path, **data) -> None:
        directory = home / ".claude" / "sessions"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{data['sessionId']}.json").write_text(json.dumps(data))

    def test_uses_durable_name_when_renamed_session_is_not_in_registry(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            cwd = "/work/project"
            self.write_transcript(
                home,
                cwd,
                "renamed-session",
                [
                    {"type": "custom-title", "customTitle": "original-name"},
                    {"type": "custom-title", "customTitle": "real-name"},
                ],
                2,
            )
            self.assertEqual(clcof.latest_session_name(cwd, home), "real-name")

    def test_newest_transcript_wins_over_unrelated_live_session(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            cwd = "/work/project"
            self.write_transcript(
                home,
                cwd,
                "older-session",
                [{"type": "custom-title", "customTitle": "main-a1231d"}],
                1,
            )
            self.write_transcript(
                home,
                cwd,
                "newer-session",
                [{"type": "custom-title", "customTitle": "real-name"}],
                2,
            )
            self.write_registry(
                home,
                sessionId="older-session",
                name="main-a1231d",
                cwd=cwd,
                updatedAt=3,
            )
            self.assertEqual(clcof.latest_session_name(cwd, home), "real-name")

    def test_registry_supplies_name_for_matching_untitled_transcript(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            cwd = "/work/project"
            self.write_transcript(home, cwd, "current-session", [], 2)
            self.write_registry(
                home,
                sessionId="current-session",
                name="registry-name",
                cwd=cwd,
                updatedAt=3,
            )
            self.assertEqual(clcof.latest_session_name(cwd, home), "registry-name")


if __name__ == "__main__":
    unittest.main()
