import contextlib
import io
import json
import unittest
from unittest.mock import patch

import rank_models as rm


def page(records):
    payload = "1:" + json.dumps(records) + "\n"
    return "<script>self.__next_f.push([1," + json.dumps(payload) + "])</script>"


def candidate(identity, effort, score, cost, creator="OpenAI"):
    return {
        "id": identity,
        "release": {"slug": "example-model", "name": "Example Model"},
        "name": f"Example Model ({effort})",
        "modelCreatorName": creator,
        "intelligenceIndex": score,
        "intelligenceIndexCostPerTask": cost,
        "price1mInputTokens": 10,
        "price1mOutputTokens": 50,
    }


class RankModelsTest(unittest.TestCase):
    def test_join_by_record_id_preserves_effort_variants_without_slugs(self):
        low = candidate("low-id", "Low", 30, 0.1)
        maximum = candidate("max-id", "Max", 50, 2)
        detail = {
            **maximum,
            "slug": "example-model",
            "effort": {"slug": "max"},
            "intelligenceIndexCostPerTask": {"cost": {"total": 2.5}},
            "intelligenceIndexOutputTokensPerTask": {"output": 100},
        }
        with patch.object(
            rm, "fetch", side_effect=[page([low, maximum]), page([detail])]
        ):
            models = [rm.flatten(record) for record in rm.aa_models()]
        self.assertEqual(
            [(m["effort"], m["intelligence"], m["cost_per_task"]) for m in models],
            [("low", 30, 0.1), ("max", 50, 2.5)],
        )
        self.assertEqual(
            models[1]["aa_url"], "https://artificialanalysis.ai/models/example-model"
        )

    def test_cost_shapes_produce_the_same_ranking(self):
        for cost in (0.5, {"total": 0.5}, {"cost": {"total": 0.5}}):
            with self.subTest(cost=cost):
                models = [
                    rm.flatten(candidate("a", "High", 40, cost)),
                    rm.flatten(candidate("b", "Max", 39, 0.6)),
                ]
                self.assertEqual(
                    [m["name"] for m in rm.pareto(models)], ["Example Model (High)"]
                )

    def test_missing_payload_is_an_error(self):
        with (
            patch.object(rm, "fetch", return_value="<html>empty</html>"),
            self.assertRaisesRegex(ValueError, "records missing"),
        ):
            rm.aa_models()

    def test_native_ladder_needs_neither_openrouter_nor_its_price_caps(self):
        records = [
            candidate("o", "Max", 50, 3),
            candidate("a", "High", 40, 2, "Anthropic"),
        ]
        output = io.StringIO()
        with (
            patch.object(rm, "aa_models", return_value=records),
            patch.object(rm, "or_index") as index,
            patch("sys.argv", ["rank_models.py", "--ladder", "openai", "--json"]),
            contextlib.redirect_stdout(output),
        ):
            rm.main()
        index.assert_not_called()
        result = json.loads(output.getvalue())
        self.assertEqual(
            [
                (m["creator"], m["effort"], m["cost_per_task"])
                for m in result["candidates"]
            ],
            [("openai", "max", 3)],
        )

    def test_openrouter_still_applies_caps_and_requires_resolution(self):
        model = rm.flatten(candidate("a", "High", 40, 0.5))
        self.assertEqual(
            rm.eligible(model),
            ["over price cap ($2/M in, $10/M out)", "no OpenRouter id"],
        )
        self.assertEqual(
            rm.eligible(
                {
                    **model,
                    "price_in": 1,
                    "price_out": 5,
                    "openrouter_id": "openai/example-model",
                }
            ),
            [],
        )

    def test_equal_cost_keeps_only_the_stronger_model(self):
        models = [
            rm.flatten(candidate("a", "High", 40, 0.5)),
            rm.flatten(candidate("b", "Max", 50, 0.5)),
        ]
        self.assertEqual([m["intelligence"] for m in rm.pareto(models)], [50])

    def test_unscored_ladder_exits_nonzero(self):
        with (
            patch.object(
                rm, "aa_models", return_value=[candidate("a", "High", None, None)]
            ),
            patch("sys.argv", ["rank_models.py", "--ladder", "openai", "--json"]),
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as raised,
        ):
            rm.main()
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
