import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY = ROOT / "loadout/skills/codebase-review/scripts/discover.py"
COLLECTOR = ROOT / "loadout/kits/skills/codebase-review-typescript/scripts/collect.py"


def module(path):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(path.stem, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class DiscoveryTests(unittest.TestCase):
    def test_rendered_copies_are_one_extension_and_conflicts_are_visible(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for directory in (".agents/skills", ".claude/skills"):
                skill = root / directory / "codebase-review-typescript"
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text("same guidance")
            custom = root / ".agents/skills/codebase-review-project"
            custom.mkdir()
            (custom / "SKILL.md").write_text("custom guidance")
            discovery = module(DISCOVERY)
            found = discovery.discover(root, "codex")
            self.assertEqual(
                [entry["name"] for entry in found],
                ["codebase-review-project", "codebase-review-typescript"],
            )
            selected = found[1]
            self.assertEqual(
                selected["path"],
                str(root / ".agents/skills/codebase-review-typescript/SKILL.md"),
            )
            self.assertEqual(len(selected["copies"]), 2)
            self.assertEqual(selected["conflict"], False)
            (root / ".claude/skills/codebase-review-typescript/helper.py").write_text(
                "different helper"
            )
            self.assertEqual(discovery.discover(root, "codex")[1]["conflict"], True)


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.git("init", "-q")

    def git(self, *arguments):
        return subprocess.run(
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                *arguments,
            ],
            cwd=self.repo,
            capture_output=True,
            text=True,
            check=True,
            timeout=20,
        ).stdout.strip()

    def write(self, path, text):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        return self.git("rev-parse", "HEAD")

    def collect(self, revision, scope="src", config="tsconfig.json", output="result"):
        target = self.base / output
        process = subprocess.run(
            [
                sys.executable,
                str(COLLECTOR),
                "--root",
                str(self.repo),
                "--ref",
                revision,
                "--scope",
                scope,
                "--tsconfig",
                config,
                "--output",
                str(target),
            ],
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        return process, json.loads((target / "summary.json").read_text())

    @unittest.skipUnless(
        shutil.which("node") and shutil.which("npm"), "Node and npm required"
    )
    def test_committed_alias_cycle_survives_dirty_source_and_config(self):
        self.write(
            "tsconfig.json",
            json.dumps(
                {"compilerOptions": {"baseUrl": ".", "paths": {"@/*": ["src/*"]}}}
            ),
        )
        self.write(
            "src/a.ts", "import { b } from '@/b'; export function a() { return b(); }\n"
        )
        self.write(
            "src/b.ts", "import { a } from '@/a'; export function b() { return a; }\n"
        )
        self.write("src/b.test.ts", "import './missing-test-helper';\n")
        self.write("src/generated/types.ts", "import './missing-generator-helper';\n")
        self.write(
            "packages/other/tsconfig.json",
            json.dumps(
                {"compilerOptions": {"baseUrl": ".", "paths": {"#/*": ["src/*"]}}}
            ),
        )
        self.write(
            "packages/other/src/x.ts",
            "import { y } from '#/y'; export function x() { return y(); }\n",
        )
        self.write(
            "packages/other/src/y.ts",
            "import { x } from '#/x'; export function y() { return x; }\n",
        )
        revision = self.commit()
        self.write("src/b.ts", "export const b = () => 1;\n")
        self.write("tsconfig.json", "invalid working-tree config")
        before = self.git("diff")
        process, result = self.collect(revision)
        self.assertEqual(
            process.returncode, 0, process.stdout + process.stderr + str(result)
        )
        self.assertEqual(result["baseline"], revision)
        self.assertEqual(result["inputs"], ["src/a.ts", "src/b.ts"])
        self.assertEqual(
            result["graph"]["clusters"][0]["files"], ["src/a.ts", "src/b.ts"]
        )
        self.assertEqual(result["complexity"]["files"], 2)
        self.assertEqual(self.git("diff"), before)
        process, nested = self.collect(
            revision, "packages/other/src", "packages/other/tsconfig.json", "nested"
        )
        self.assertEqual(process.returncode, 0, str(nested))
        self.assertEqual(
            nested["graph"]["clusters"][0]["files"],
            ["packages/other/src/x.ts", "packages/other/src/y.ts"],
        )

    @unittest.skipUnless(
        shutil.which("node") and shutil.which("npm"), "Node and npm required"
    )
    def test_unresolved_imports_are_partial_and_reports_are_preserved(self):
        self.write("tsconfig.json", "{}")
        self.write(
            "src/a.ts",
            "import { missing } from './missing'; export const a = missing();\n",
        )
        revision = self.commit()
        process, result = self.collect(revision)
        self.assertEqual(process.returncode, 2)
        self.assertEqual(result["graph"]["status"], "partial")
        self.assertEqual(result["graph"]["unresolved"][0]["unresolvedTo"], "./missing")
        self.assertEqual(result["complexity"]["status"], "complete")
        report = (self.base / "result/summary.json").read_bytes()
        process, _ = self.collect(revision)
        self.assertEqual(process.returncode, 2)
        self.assertEqual((self.base / "result/summary.json").read_bytes(), report)

    def test_invalid_revision_is_a_failed_report(self):
        process, result = self.collect("missing-revision")
        self.assertEqual(process.returncode, 2)
        self.assertEqual(result["status"], "failed")

    @unittest.skipUnless(
        shutil.which("node") and shutil.which("npm"), "Node and npm required"
    )
    def test_workspace_links_resolve_to_the_baseline(self):
        self.write("tsconfig.json", "{}")
        self.write(
            "package.json", json.dumps({"private": True, "workspaces": ["packages/*"]})
        )
        for name, other in (("a", "b"), ("b", "a")):
            self.write(
                f"packages/{name}/package.json",
                json.dumps({"name": name, "main": "index.ts"}),
            )
            self.write(
                f"packages/{name}/index.ts",
                f"import {{ {other} }} from '{other}'; export function {name}() {{ return {other}; }}\n",
            )
        revision = self.commit()
        dependencies = self.repo / "node_modules"
        dependencies.mkdir()
        for name in ("a", "b"):
            (dependencies / name).symlink_to(
                self.repo / "packages" / name, target_is_directory=True
            )
        self.write("packages/b/index.ts", "export function b() { return 1; }\n")
        process, result = self.collect(revision, "packages")
        self.assertEqual(process.returncode, 0, str(result))
        self.assertEqual(
            result["graph"]["clusters"][0]["files"],
            ["packages/a/index.ts", "packages/b/index.ts"],
        )
        self.assertEqual(result["graph"]["source_outside_snapshot"], [])


if __name__ == "__main__":
    unittest.main()
