import json
import os
import re
import shlex
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

STATUSLINE = Path(__file__).with_name("statusline.sh")
TIMEZONE = ZoneInfo("Europe/Berlin")
RESET_AT = datetime(2026, 8, 29, 10, tzinfo=TIMEZONE)


def calculate_fields(at: datetime) -> dict[str, str]:
    source = STATUSLINE.read_text()
    match = re.search(r"\| jq .*? -r '\n(.*?)'\)\"\n", source, re.DOTALL)
    if match is None:
        raise RuntimeError("statusline jq program not found")

    payload = {
        "workspace": {"current_dir": "/tmp/project"},
        "model": {"display_name": "Test"},
        "output_style": {"name": "default"},
        "context_window": {"used_percentage": 0},
        "rate_limits": {
            "seven_day": {
                "used_percentage": 21,
                "resets_at": RESET_AT.timestamp(),
            }
        },
    }
    env = os.environ.copy()
    env["TZ"] = "Europe/Berlin"
    result = subprocess.run(
        [
            "jq",
            "-r",
            "-L",
            str(STATUSLINE.parent),
            "--argjson",
            "test_now",
            str(at.timestamp()),
            match.group(1).replace(
                'include "weekly-usage";',
                'include "weekly-usage";\ndef now: $test_now;',
            ),
        ],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )
    return dict(part.split("=", 1) for part in shlex.split(result.stdout))


class StatuslineUsageTest(unittest.TestCase):
    def test_daily_allowance_advances_at_five_am_local_time(self) -> None:
        before = calculate_fields(datetime(2026, 8, 24, 4, 59, tzinfo=TIMEZONE))
        after = calculate_fields(datetime(2026, 8, 24, 5, 0, tzinfo=TIMEZONE))

        self.assertEqual(before["seven_today"], "8")
        self.assertEqual(after["seven_today"], "22")

    def test_reset_countdown_remains_exact(self) -> None:
        at = datetime(2026, 8, 24, 9, 20, tzinfo=TIMEZONE)

        fields = calculate_fields(at)

        self.assertEqual(
            fields["seven_left"], str(int(RESET_AT.timestamp() - at.timestamp()))
        )

    def test_captures_current_weekly_usage_across_session_redraws(self) -> None:
        reset = (datetime.now(TIMEZONE) + timedelta(days=3)).timestamp()
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, XDG_DATA_HOME=directory)
            env.pop("ANTHROPIC_BASE_URL", None)
            capture = Path(directory) / "ringleader/claude-limits.json"

            for used, resets_at, expected in (
                (60, reset, 60),
                (41, reset, 60),
                (62, reset, 62),
                (3, reset + 604800, 3),
            ):
                weekly = {"used_percentage": used, "resets_at": resets_at}
                payload = {"cwd": directory, "rate_limits": {"seven_day": weekly}}
                subprocess.run(
                    ["bash", str(STATUSLINE), "--capture-usage"],
                    input=json.dumps(payload),
                    env=env,
                    text=True,
                    capture_output=True,
                    timeout=5,
                    check=True,
                )
                self.assertEqual(
                    json.loads(capture.read_text())["rate_limits"]["seven_day"],
                    {"used_percentage": expected, "resets_at": resets_at},
                )


if __name__ == "__main__":
    unittest.main()
