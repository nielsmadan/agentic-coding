import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import extraction_benchmark as bench
from extraction_cases import cases, grade


class BenchmarkTests(unittest.TestCase):
    def test_expected_answers_pass(self):
        for case in cases():
            with self.subTest(case=case.name):
                self.assertTrue(grade(case, case.expected))

    def test_quote_fabrication_and_wrong_subject_fail(self):
        selected = {case.name: case for case in cases()}
        self.assertFalse(
            grade(
                selected["quotes"],
                selected["quotes"].expected + "\nThe queue deletes all jobs.",
            )
        )
        self.assertFalse(
            grade(
                selected["partial-match"],
                "A predictable branch avoids pipeline stalls.",
            )
        )
        self.assertFalse(
            grade(
                selected["code"],
                "delay = min(2 ** attempt, 12)\nqueue.put((job_id, delay))",
            )
        )
        self.assertFalse(grade(selected["embedded-instructions"], "900 hours"))

    def test_measure_does_not_fallback_and_unknown_cost_is_null(self):
        payload = {
            "choices": [{"message": {"content": cases()[0].expected}}],
            "model": "test",
        }
        with mock.patch.object(
            bench.extraction, "request_extract", return_value=payload
        ):
            row = bench.measure("test", cases()[0], 1, 1)
        self.assertTrue(row["passed"])
        self.assertIsNone(row["cost_usd"])
        with mock.patch.object(
            bench.extraction,
            "request_extract",
            side_effect=bench.extraction.ExtractError("busy", True),
        ) as call:
            row = bench.measure("test", cases()[0], 1, 1)
        self.assertEqual(row["error"], "busy")
        self.assertEqual(call.call_count, 1)

    def test_budget_stops_before_request_and_saves_partial_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            models = Path(tmp, "models.txt")
            models.write_text("test\n")
            out = Path(tmp, "result")
            opts = argparse.Namespace(
                modelfile=models,
                outdir=out,
                repeats=1,
                workers=1,
                budget=0.01,
                timeout=1,
            )
            with (
                mock.patch.object(bench, "candidate_info", return_value={"test": {}}),
                mock.patch.object(bench, "reserve_cost", return_value=1),
                mock.patch.object(bench, "measure") as measure,
            ):
                self.assertEqual(bench.run(opts), 2)
            measure.assert_not_called()
            summary = json.loads((out / "summary.json").read_text())
            self.assertTrue(summary["budget_stopped"])
            self.assertEqual(summary["models"][0]["calls"], 0)

    def test_unknown_cost_keeps_reservation_and_stops_next_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            models = Path(tmp, "models.txt")
            models.write_text("test\n")
            out = Path(tmp, "result")
            opts = argparse.Namespace(
                modelfile=models,
                outdir=out,
                repeats=1,
                workers=1,
                budget=1.5,
                timeout=1,
            )
            row = {
                "model": "test",
                "case": "relevant",
                "passed": True,
                "cost_usd": None,
                "latency_s": 0.1,
            }
            with (
                mock.patch.object(bench, "candidate_info", return_value={"test": {}}),
                mock.patch.object(bench, "reserve_cost", return_value=1),
                mock.patch.object(bench, "measure", return_value=row) as measure,
            ):
                self.assertEqual(bench.run(opts), 2)
            self.assertEqual(measure.call_count, 1)
            summary = json.loads((out / "summary.json").read_text())
            self.assertEqual(summary["budget_charge_usd"], 1)
            self.assertEqual(summary["models"][0]["unknown_cost_calls"], 1)
            saved = json.loads((out / "responses.jsonl").read_text())
            self.assertIsNone(saved["cost_usd"])

    def test_complete_run_retains_all_answers_and_costs(self):
        with tempfile.TemporaryDirectory() as tmp:
            models = Path(tmp, "models.txt")
            models.write_text("test\n")
            out = Path(tmp, "result")
            opts = argparse.Namespace(
                modelfile=models, outdir=out, repeats=1, workers=2, budget=5, timeout=1
            )

            def measure(model, case, repetition, timeout):
                return {
                    "model": model,
                    "case": case.name,
                    "passed": True,
                    "answer": case.expected,
                    "cost_usd": 0.01,
                    "latency_s": 0.1,
                }

            with (
                mock.patch.object(bench, "candidate_info", return_value={"test": {}}),
                mock.patch.object(bench, "reserve_cost", return_value=0.1),
                mock.patch.object(bench, "measure", side_effect=measure),
            ):
                self.assertEqual(bench.run(opts), 0)
            saved = [
                json.loads(line)
                for line in (out / "responses.jsonl").read_text().splitlines()
            ]
            self.assertEqual(
                {r["case"]: r["answer"] for r in saved},
                {c.name: c.expected for c in cases()},
            )
            summary = json.loads((out / "summary.json").read_text())
            self.assertTrue(summary["complete"])
            self.assertAlmostEqual(summary["models"][0]["known_cost_usd"], 0.08)


if __name__ == "__main__":
    unittest.main()
