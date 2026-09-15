import io
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import statusline


NOW = datetime.fromisoformat("2026-09-14T19:40:00+00:00").timestamp()
LIMITS = {
    "standard": {
        "weekly": {"usedPercent": 15, "windowEnd": "2026-09-21T09:40:00Z"},
        "fiveHour": {"usedPercent": 96},
        "monthly": {"usedPercent": 4},
    },
    "core": {"weekly": {"usedPercent": 90}},
}


def plain(text):
    return statusline.ANSI.sub("", text)


class UsageTest(unittest.TestCase):
    def test_inclusive_totals_cover_subagents_without_double_counting(self):
        session = {
            "tokenUsage": {"factoryCredits": 1000, "inputTokens": 100, "cacheReadTokens": 100},
            "inclusiveTokenUsage": {
                "factoryCredits": 2500,
                "inputTokens": 100,
                "cacheCreationTokens": 100,
                "cacheReadTokens": 800,
                "outputTokens": 900,
                "thinkingTokens": 300,
            },
            "childInclusiveTokenUsageBySessionId": {"child": {"factoryCredits": 1500}},
        }

        result = [plain(text) for _, text in statusline.usage_segments(session, None, NOW)]

        self.assertEqual(result, ["7d ?", "🪙 2.5K cr", "♻ 80%"])

    def test_own_totals_are_used_when_inclusive_totals_are_missing(self):
        session = {"tokenUsage": {"factoryCredits": 0, "inputTokens": 100, "cacheReadTokens": 300}}

        result = [plain(text) for _, text in statusline.usage_segments(session, None, NOW)]

        self.assertEqual(result, ["7d ?", "🪙 0 cr", "♻ 75%"])

    def test_standard_windows_keep_server_percentages_and_weekly_reset(self):
        result = [plain(text) for _, text in statusline.usage_segments({}, LIMITS, NOW)]

        self.assertEqual(result, ["5h 96%", "7d 15% 6d14h", "30d 4%"])

    def test_missing_and_expired_windows_are_unknown(self):
        for bucket in (None, {}, {"usedPercent": 15, "windowEnd": "2026-09-14T09:40:00Z"}):
            with self.subTest(bucket=bucket):
                self.assertEqual(plain(statusline.window_segment("7d", bucket, NOW)), "7d ?")

    def test_unused_window_is_zero_without_a_reset_countdown(self):
        bucket = {"usedPercent": 0, "windowEnd": None}

        self.assertEqual(plain(statusline.window_segment("7d", bucket, NOW, True)), "7d 0%")

    def test_narrow_layout_retains_weekly_and_shorter_limit_first(self):
        session = {"tokenUsage": {"factoryCredits": 2500, "inputTokens": 100, "cacheReadTokens": 300}}
        segments = statusline.usage_segments(session, LIMITS, NOW)

        result = statusline.fit_usage(segments, 25)

        self.assertEqual(plain(result), "5h 96% │ 7d 15% 6d14h")
        self.assertLessEqual(statusline.display_width(result), 25)
        self.assertEqual(plain(statusline.fit_usage(segments, 30)), "5h 96% │ 7d 15% 6d14h │ 30d 4%")
        self.assertEqual(plain(statusline.fit_usage(segments, 16)), "7d 15% 6d14h")

    def test_missing_session_file_does_not_prevent_account_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            session = statusline.read_json(Path(directory) / "missing.settings.json")

        self.assertEqual(
            [plain(text) for _, text in statusline.usage_segments(session, LIMITS, NOW)],
            ["5h 96%", "7d 15% 6d14h", "30d 4%"],
        )


class LayoutTest(unittest.TestCase):
    def test_usage_is_right_aligned_on_one_row(self):
        renderer = Path(__file__).parents[1] / "claude/hooks/statusline.sh"
        payload = {
            "cwd": "/tmp",
            "model": {"display_name": "Claude Opus 4.6"},
            "context_window": {"used_percentage": 25},
            "effort": {"level": "high"},
        }
        session = {"tokenUsage": {"factoryCredits": 2500, "inputTokens": 100, "cacheReadTokens": 300}}
        segments = statusline.usage_segments(session, LIMITS, NOW)

        for width in (40, 80, 120):
            with self.subTest(width=width), patch.dict("os.environ", {"AGENT_SANDBOX": "1"}):
                result = statusline.render_line(payload, segments, width, renderer)

                self.assertEqual(len(result.splitlines()), 1)
                self.assertEqual(statusline.display_width(result), width - 2)
                self.assertTrue(plain(result).startswith("🔒"))
                if width == 120:
                    self.assertIn("🤖 opus4.6", plain(result))
                    self.assertTrue(plain(result).endswith("5h 96% │ 7d 15% 6d14h │ 30d 4% │ 🪙 2.5K cr │ ♻ 75%"))
                elif width == 80:
                    self.assertTrue(plain(result).endswith("5h 96% │ 7d 15% 6d14h │ 30d 4%"))
                else:
                    self.assertTrue(plain(result).endswith("7d 15% 6d14h"))

    def test_tiny_widths_still_fit_one_row(self):
        segments = statusline.usage_segments({}, LIMITS, NOW)

        for width in (3, 8, 14):
            with self.subTest(width=width):
                result = statusline.render_line({}, segments, width, Path("unused"))

                self.assertEqual(len(result.splitlines()), 1)
                self.assertLessEqual(statusline.display_width(result), width - 2)


class LimitsCacheTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.cache_dir = Path(self.directory.name)

    def response(self):
        return io.StringIO(json.dumps({"limits": LIMITS}))

    @patch("statusline.urllib.request.urlopen")
    def test_live_response_is_cached_for_one_minute(self, urlopen):
        urlopen.side_effect = lambda *args, **kwargs: self.response()

        for now in (NOW, NOW + 59):
            self.assertEqual(statusline.load_limits("test-key", self.cache_dir, now), LIMITS)
        self.assertEqual(urlopen.call_count, 1)
        self.assertEqual(statusline.load_limits("test-key", self.cache_dir, NOW + 60), LIMITS)
        self.assertEqual(urlopen.call_count, 2)

        stored = json.loads(next(self.cache_dir.glob("*.json")).read_text())
        self.assertEqual(stored, {"checked_at": NOW + 60, "limits": LIMITS})

    @patch("statusline.urllib.request.urlopen")
    def test_network_failure_clears_stale_usage_and_throttles_retries(self, urlopen):
        urlopen.return_value = self.response()
        self.assertEqual(statusline.load_limits("test-key", self.cache_dir, NOW), LIMITS)
        urlopen.side_effect = TimeoutError

        self.assertIsNone(statusline.load_limits("test-key", self.cache_dir, NOW + 60))
        self.assertIsNone(statusline.load_limits("test-key", self.cache_dir, NOW + 119))
        self.assertEqual(urlopen.call_count, 2)

        urlopen.side_effect = lambda *args, **kwargs: self.response()
        self.assertEqual(statusline.load_limits("test-key", self.cache_dir, NOW + 120), LIMITS)

    @patch("statusline.urllib.request.urlopen")
    def test_changed_account_fetches_its_own_limits(self, urlopen):
        urlopen.side_effect = lambda *args, **kwargs: self.response()

        statusline.load_limits("first-key", self.cache_dir, NOW)
        statusline.load_limits("second-key", self.cache_dir, NOW + 1)

        self.assertEqual(urlopen.call_count, 2)
        self.assertEqual(len(list(self.cache_dir.glob("*.json"))), 2)

    @patch("statusline.urllib.request.urlopen")
    def test_missing_api_key_never_makes_a_request(self, urlopen):
        self.assertIsNone(statusline.load_limits(None, self.cache_dir, NOW))
        urlopen.assert_not_called()

    @patch("statusline.urllib.request.urlopen")
    def test_corrupt_cache_is_refreshed(self, urlopen):
        urlopen.side_effect = lambda *args, **kwargs: self.response()
        statusline.load_limits("test-key", self.cache_dir, NOW)
        cache = next(self.cache_dir.glob("*.json"))

        for content in ("{", '{"checked_at":"invalid"}', json.dumps({"checked_at": NOW, "limits": []})):
            with self.subTest(content=content):
                cache.write_text(content)
                self.assertEqual(statusline.load_limits("test-key", self.cache_dir, NOW + 1), LIMITS)


if __name__ == "__main__":
    unittest.main()
